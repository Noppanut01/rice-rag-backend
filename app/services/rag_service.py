import json
import os
import re
import time

_STRIP_ASTERISKS = re.compile(r"\*+")

from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import Docx2txtLoader, PyMuPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from app.core.config import settings


def _normalize_prompt_suggestions(items: list[dict]) -> list[dict]:
    suggestions: list[dict] = []
    seen: set[str] = set()

    for item in items:
        if not isinstance(item, dict):
            continue

        title = _STRIP_ASTERISKS.sub("", str(item.get("title", ""))).strip(" -\n\t")
        content = _STRIP_ASTERISKS.sub("", str(item.get("content", ""))).strip(" -\n\t")
        title = re.sub(r"\s+", " ", title)
        content = re.sub(r"\s+", " ", content)

        if not title or not content:
            continue
        if len(title) > 45 or len(content) > 200:
            continue
        if not content.endswith("?"):
            content = f"{content}?"

        key = content.lower()
        if key in seen:
            continue
        seen.add(key)
        suggestions.append({"title": title, "content": content})

        if len(suggestions) == 5:
            break

    return suggestions


def _extract_token_usage(raw) -> tuple[int, int]:
    usage = getattr(raw, "usage_metadata", None) or {}
    response_metadata = getattr(raw, "response_metadata", {}) or {}
    response_usage = response_metadata.get("usage_metadata", {}) or {}
    token_usage = response_metadata.get("token_usage", {}) or {}

    input_tokens = (
        usage.get("input_tokens")
        or response_usage.get("input_tokens")
        or response_usage.get("prompt_token_count")
        or token_usage.get("input_tokens")
        or token_usage.get("prompt_tokens")
        or 0
    )
    output_tokens = (
        usage.get("output_tokens")
        or response_usage.get("output_tokens")
        or response_usage.get("candidates_token_count")
        or token_usage.get("output_tokens")
        or token_usage.get("completion_tokens")
        or 0
    )
    return int(input_tokens or 0), int(output_tokens or 0)


class RAGService:
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=f"models/{settings.GEMINI_EMBEDDING_MODEL}",
            google_api_key=settings.GEMINI_API_KEY,
        )
        self.vectorstores: dict[str, Chroma] = {}
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=settings.LLM_TEMPERATURE,
        )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

    def _build_history_text(self, history: list[dict] | None) -> str:
        if not history:
            return ""
        recent = history[-10:]
        lines = "".join(
            ("ผู้ใช้" if msg.get("role") == "user" else "ระบบ")
            + ": "
            + str(msg.get("content"))
            + "\n"
            for msg in recent
        )
        return f"ประวัติการสนทนาก่อนหน้า:\n{lines}\n"

    def load_collections(self, names: list[str]):
        for name in names:
            if name not in self.vectorstores:
                self.vectorstores[name] = Chroma(
                    collection_name=name,
                    embedding_function=self.embeddings,
                    persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
                )

    def _search(self, collections: list[str], question: str) -> list:
        all_docs = []
        for name in collections:
            vs = self.vectorstores.get(name)
            if vs is None:
                continue
            try:
                if vs._collection.count() == 0:
                    continue
                if settings.RETRIEVAL_STRATEGY == "mmr":
                    docs = vs.max_marginal_relevance_search(
                        question, k=settings.RETRIEVAL_K, fetch_k=10
                    )
                else:
                    docs = vs.similarity_search(question, k=settings.RETRIEVAL_K)
                all_docs.extend(docs)
            except Exception:
                pass
        seen = set()
        unique = []
        for doc in all_docs:
            key = doc.page_content[:80]
            if key not in seen:
                seen.add(key)
                unique.append(doc)
        return unique[: settings.RETRIEVAL_K * 2]

    def _load_pdf_documents(self, file_path: str) -> list[Document]:
        docs = PyMuPDFLoader(file_path).load()
        for doc in docs:
            doc.metadata["extraction_method"] = "pymupdf"
        return docs

    def ingest_document(self, file_path: str, collection_name: str) -> str:
        file_path = os.path.abspath(file_path)
        if file_path.endswith(".pdf"):
            docs = self._load_pdf_documents(file_path)
        elif file_path.endswith(".docx"):
            loader = Docx2txtLoader(file_path)
            docs = loader.load()
        else:
            loader = TextLoader(file_path, encoding="utf-8")
            docs = loader.load()

        chunks = self.splitter.split_documents(docs)
        if collection_name not in self.vectorstores:
            self.vectorstores[collection_name] = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
            )
        self.vectorstores[collection_name].add_documents(chunks)
        return collection_name

    def ask_question(
        self,
        question: str,
        plan_context: str | None = None,
        collection: str | None = None,
        history: list[dict] | None = None,
    ) -> dict:
        start = time.time()

        all_collections = list(self.vectorstores.keys())
        if collection and collection in self.vectorstores:
            search_cols = list({collection, "general"} & set(all_collections))
        else:
            search_cols = all_collections

        docs = self._search(search_cols, question)
        context = "\n\n".join([doc.page_content for doc in docs])
        if plan_context:
            context = f"{plan_context}\n\nเอกสารอ้างอิง:\n{context}"

        seen_sources = set()
        sources = []
        for doc in docs:
            src = os.path.basename(doc.metadata.get("source", ""))
            if src and src not in seen_sources:
                seen_sources.add(src)
                sources.append(src)

        history_text = self._build_history_text(history)

        prompt = PromptTemplate(
            template=(
                "คุณคือ AI ผู้ช่วยด้านการปลูกข้าว\n"
                "กฎในการตอบคำถาม:\n"
                "1. ให้ตอบโดยอ้างอิงจากข้อมูลสนับสนุน (Context) เป็นหลัก\n"
                "2. ถ้า Context มีข้อมูลที่เกี่ยวข้อง ให้ใช้ข้อมูลนั้นก่อน และห้ามตอบขัดแย้งกับ Context\n"
                "3. ต้องตอบให้ตรงเงื่อนไขสำคัญในคำถาม เช่น พันธุ์ สถานที่ วิธีปลูก โรค สารเคมี อัตรา หรือช่วงเวลา\n"
                "4. ถ้า Context ไม่มีคำตอบตรงเงื่อนไขสำคัญ หรือมีเพียงข้อมูลใกล้เคียง ให้บอกส่วนที่พบจาก Context และตอบคำแนะนำทั่วไปได้เฉพาะเบื้องต้น\n"
                "5. หากตอบจากความรู้ทั่วไป ต้องต่อท้ายคำตอบด้วยข้อความนี้เสมอ: [หมายเหตุ: คำตอบนี้ใช้ความรู้ทั่วไป เนื่องจากไม่พบในเอกสารอ้างอิง]\n"
                "6. ห้ามแต่งตัวเลขเฉพาะ เช่น อายุเก็บเกี่ยว อัตราปุ๋ย ปริมาณสารเคมี หรือช่วงวันที่ หากไม่มีใน Context\n"
                "7. ตอบเป็นภาษาไทย กระชับ เข้าใจง่าย ไม่เกิน 5 ประโยค\n\n"
                "{history_text}"
                "ข้อมูลสนับสนุน (Context):\n{context}\n\n"
                "คำถามปัจจุบัน: {question}\n"
                "คำตอบ:"
            ),
            input_variables=["context", "question", "history_text"],
        )
        raw = (prompt | self.llm).invoke(
            {"context": context, "question": question, "history_text": history_text}
        )
        input_tokens, output_tokens = _extract_token_usage(raw)
        answer = _STRIP_ASTERISKS.sub(
            "", str(raw.content) if hasattr(raw, "content") else raw
        ).strip()

        return {
            "answer": answer,
            "sources": sources,
            "model_used": settings.GEMINI_MODEL,
            "embedding_model": settings.GEMINI_EMBEDDING_MODEL,
            "retrieval_strategy": settings.RETRIEVAL_STRATEGY,
            "chunk_size": settings.CHUNK_SIZE,
            "retrieval_k": settings.RETRIEVAL_K,
            "chunks_retrieved": len(docs),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "response_time_ms": round((time.time() - start) * 1000),
        }

    def generate_prompt_suggestions(self) -> list[dict]:
        query = "การปลูกข้าว การดูแลรักษา ปุ๋ย โรคและแมลง การจัดการน้ำ การเก็บเกี่ยว"
        docs = self._search(list(self.vectorstores.keys()), query)
        context = "\n\n".join([doc.page_content for doc in docs])[:12000]

        prompt = PromptTemplate(
            template=(
                "คุณคือผู้ช่วยออกแบบ prompt template สำหรับแชตบอทผู้เชี่ยวชาญเรื่องข้าว\n"
                "Prompt template ในระบบนี้คือคำถามตัวอย่างที่ผู้ใช้กดแล้วจะถูกใส่ในช่องแชต "
                "ไม่ใช่ system prompt และไม่ใช่คำตอบ\n\n"
                "ให้สร้างคำถามแนะนำ 5 รายการสำหรับเกษตรกรผู้ปลูกข้าว โดยอิงจากเนื้อหาที่ให้มา "
                "ถ้าเนื้อหามีน้อย ให้ใช้หัวข้อความรู้พื้นฐานด้านการปลูกข้าว\n\n"
                "กฎการสร้าง:\n"
                "- ใช้ภาษาไทยเท่านั้น\n"
                "- title ต้องเป็นชื่อสั้น 2-5 คำ เช่น การใส่ปุ๋ย, โรคข้าว, จัดการน้ำ\n"
                "- content ต้องเป็นคำถามเดียวที่เกษตรกรจะถามจริง ความยาวไม่เกิน 120 ตัวอักษร และลงท้ายด้วยเครื่องหมาย ?\n"
                "- ห้ามเขียนคำตอบ ห้ามอธิบาย ห้ามใส่ markdown ห้ามใส่ placeholder\n"
                "- แต่ละรายการต้องถามคนละประเด็น เช่น พันธุ์ข้าว วันที่ปลูก วิธีปลูก ปุ๋ย น้ำ โรคแมลง หรือเก็บเกี่ยว\n"
                '- ห้ามสร้างคำถามซ้ำหรือกว้างเกินไป เช่น "ปลูกข้าวอย่างไร?"\n\n'
                "ตอบเป็น JSON array เท่านั้น โดยใช้ schema นี้เท่านั้น:\n"
                '[{{"title":"ชื่อสั้น","content":"คำถามเต็ม?"}}]\n\n'
                "เนื้อหา:\n{context}\n\n"
                "JSON:"
            ),
            input_variables=["context"],
        )
        llm_creative = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.4,
        )
        raw = (prompt | llm_creative).invoke({"context": context})
        raw = str(raw.content) if hasattr(raw, "content") else raw
        raw = raw.strip()

        try:
            match = re.search(r"\[.*\]", raw, re.DOTALL)
            if match:
                result = json.loads(match.group())
                return _normalize_prompt_suggestions(result)
        except Exception:
            pass
        return [
            {
                "title": "เลือกพันธุ์ข้าว",
                "content": "ควรเลือกพันธุ์ข้าวแบบใดให้เหมาะกับพื้นที่และฤดูกาลปลูก?",
            },
            {
                "title": "วันที่ปลูก",
                "content": "ควรเริ่มปลูกข้าวช่วงเดือนไหนจึงเหมาะกับพันธุ์ที่ไวต่อช่วงแสง?",
            },
            {"title": "การใส่ปุ๋ย", "content": "ควรใส่ปุ๋ยข้าวช่วงใดและใช้สูตรปุ๋ยอะไรจึงเหมาะสม?"},
            {
                "title": "จัดการน้ำ",
                "content": "ควรจัดการระดับน้ำในนาอย่างไรในแต่ละช่วงการเจริญเติบโตของข้าว?",
            },
            {
                "title": "โรคและแมลง",
                "content": "ถ้าข้าวมีอาการผิดปกติควรตรวจโรคหรือแมลงศัตรูข้าวอย่างไร?",
            },
        ]

    def ask_question_no_rag(
        self,
        question: str,
        plan_context: str | None = None,
        history: list[dict] | None = None,
    ) -> dict:
        start = time.time()

        context = plan_context if plan_context else ""

        history_text = self._build_history_text(history)

        prompt = PromptTemplate(
            template=(
                "ตอบคำถามเป็นภาษาไทย ไม่เกิน 5 ประโยค\n\n"
                "{history_text}"
                "{context}"
                "คำถามปัจจุบัน: {question}\n"
                "คำตอบ:"
            ),
            input_variables=["context", "question", "history_text"],
        )
        raw = (prompt | self.llm).invoke(
            {"context": context, "question": question, "history_text": history_text}
        )
        input_tokens, output_tokens = _extract_token_usage(raw)
        answer = _STRIP_ASTERISKS.sub(
            "", str(raw.content) if hasattr(raw, "content") else raw
        ).strip()

        return {
            "answer": answer,
            "sources": [],
            "model_used": settings.GEMINI_MODEL,
            "embedding_model": "",
            "retrieval_strategy": "none",
            "chunk_size": 0,
            "retrieval_k": 0,
            "chunks_retrieved": 0,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "response_time_ms": round((time.time() - start) * 1000),
        }

    def delete_document(self, file_path: str, collection_name: str):
        file_path = os.path.abspath(file_path)
        vs = self.vectorstores.get(collection_name)
        if vs:
            vs._collection.delete(where={"source": file_path})
        if os.path.exists(file_path):
            os.remove(file_path)


rag_service = RAGService()
