import json
import os
import re
import time

from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from app.core.config import settings


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
                    docs = vs.max_marginal_relevance_search(question, k=settings.RETRIEVAL_K, fetch_k=10)
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
        return unique[:settings.RETRIEVAL_K * 2]

    def ingest_document(self, file_path: str, collection_name: str) -> str:
        file_path = os.path.abspath(file_path)
        if file_path.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        elif file_path.endswith(".docx"):
            loader = Docx2txtLoader(file_path)
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

    def ask_question(self, question: str, plan_context: str | None = None, collection: str | None = None, history: list[dict] | None = None) -> dict:
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

        history_text = ""
        if history:
            # ใช้ 10 ข้อความล่าสุด (5 คู่ ถาม-ตอบ)
            recent_history = history[-10:]
            for msg in recent_history:
                role = "ผู้ใช้" if msg.get("role") == "user" else "ระบบ"
                history_text += f"{role}: {msg.get('content')}\n"
            history_text = f"ประวัติการสนทนาก่อนหน้า:\n{history_text}\n"

        prompt = PromptTemplate(
            template=(
                "ใช้ข้อมูลด้านล่างตอบคำถามอ้างอิงกับประวัติการสนทนา ถ้าไม่มีข้อมูลให้บอกว่าไม่ทราบ\n"
                "ตอบเป็นภาษาไทย ไม่เกิน 5 ประโยค\n\n"
                "{history_text}"
                "ข้อมูลที่เกี่ยวข้อง:\n{context}\n\n"
                "คำถามปัจจุบัน: {question}\n"
                "คำตอบ:"
            ),
            input_variables=["context", "question", "history_text"],
        )
        answer = (prompt | self.llm).invoke({"context": context, "question": question, "history_text": history_text})
        answer = re.sub(r'\*+', '', str(answer.content) if hasattr(answer, 'content') else answer).strip()

        return {
            "answer": answer,
            "sources": sources,
            "model_used": settings.GEMINI_MODEL,
            "embedding_model": settings.GEMINI_EMBEDDING_MODEL,
            "retrieval_strategy": settings.RETRIEVAL_STRATEGY,
            "chunk_size": settings.CHUNK_SIZE,
            "chunks_retrieved": len(docs),
            "response_time_ms": round((time.time() - start) * 1000),
        }

    def generate_prompt_suggestions(self) -> list[dict]:
        query = "การปลูกข้าว การดูแลรักษา ปุ๋ย โรคและแมลง การจัดการน้ำ การเก็บเกี่ยว"
        docs = self._search(list(self.vectorstores.keys()), query)
        context = "\n\n".join([doc.page_content for doc in docs])

        prompt = PromptTemplate(
            template=(
                "จากเนื้อหาต่อไปนี้ สร้างคำถามที่มีประโยชน์สำหรับเกษตรกรผู้ปลูกข้าว 5 ข้อ\n"
                "แต่ละข้อมี title (ชื่อสั้นๆ) และ content (คำถามเต็ม)\n"
                "ตอบเป็น JSON array เท่านั้น ห้ามมีข้อความอื่น ห้ามมี markdown\n\n"
                "เนื้อหา:\n{context}\n\n"
                'ตัวอย่าง output: [{{"title": "การใส่ปุ๋ย", "content": "ควรใส่ปุ๋ยข้าวหอมมะลิตอนไหนและใช้ปุ๋ยชนิดใด?"}}, ...]\n\n'
                "JSON:"
            ),
            input_variables=["context"],
        )
        llm_creative = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.7,
        )
        raw = (prompt | llm_creative).invoke({"context": context})
        raw = str(raw.content) if hasattr(raw, 'content') else raw
        raw = raw.strip()

        try:
            match = re.search(r'\[.*\]', raw, re.DOTALL)
            if match:
                result = json.loads(match.group())
                return [r for r in result if isinstance(r, dict) and "title" in r and "content" in r]
        except Exception:
            pass
        return []

    def ask_question_no_rag(self, question: str, plan_context: str | None = None, history: list[dict] | None = None) -> dict:
        start = time.time()

        if plan_context:
            question = f"{plan_context}\n\nคำถาม: {question}"

        history_text = ""
        if history:
            recent_history = history[-10:]
            for msg in recent_history:
                role = "ผู้ใช้" if msg.get("role") == "user" else "ระบบ"
                history_text += f"{role}: {msg.get('content')}\n"
            history_text = f"ประวัติการสนทนาก่อนหน้า:\n{history_text}\n"

        prompt = PromptTemplate(
            template=(
                "ตอบคำถามต่อไปนี้จากความรู้ทั่วไปของคุณ ตอบเป็นภาษาไทย\n\n"
                "{history_text}"
                "คำถามปัจจุบัน: {question}\n\n"
                "คำตอบ:"
            ),
            input_variables=["question", "history_text"],
        )
        answer = (prompt | self.llm).invoke({"question": question, "history_text": history_text})
        answer = str(answer.content) if hasattr(answer, 'content') else answer

        return {
            "answer": answer,
            "sources": [],
            "model_used": settings.GEMINI_MODEL,
            "embedding_model": "",
            "retrieval_strategy": "none",
            "chunk_size": 0,
            "chunks_retrieved": 0,
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
