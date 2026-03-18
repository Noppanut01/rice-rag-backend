import os
import re
import time

import psutil
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_ollama import OllamaEmbeddings, OllamaLLM

from app.core.config import settings

COLLECTIONS = ["jasmine", "rd43", "kk15", "pathumthani", "general"]

VARIETY_COLLECTION_MAP = {
    "jasmine": "jasmine",
    "rd43": "rd43",
    "kk15": "kk15",
    "pathumthani": "pathumthani",
}


class RAGService:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(
            model=settings.OLLAMA_EMBEDDING_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
        )
        self.vectorstores = {
            name: Chroma(
                collection_name=name,
                embedding_function=self.embeddings,
                persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
            )
            for name in COLLECTIONS
        }
        self.llm = OllamaLLM(
            model=settings.OLLAMA_LLM_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=settings.LLM_TEMPERATURE,
        )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
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
        vs = self.vectorstores.get(collection_name)
        if vs is None:
            vs = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
            )
            self.vectorstores[collection_name] = vs
        vs.add_documents(chunks)
        return collection_name

    def ask_question(self, question: str, collection: str | None = None, history: list[dict] | None = None) -> dict:
        start = time.time()
        ram_before = psutil.Process().memory_info().rss / 1024 / 1024

        if collection and collection in COLLECTIONS:
            docs = self._search([collection, "general"], question)
        else:
            docs = self._search(COLLECTIONS, question)

        context = "\n\n".join([doc.page_content for doc in docs])
        seen_sources = set()
        sources = []
        for doc in docs:
            src = os.path.basename(doc.metadata.get("source", ""))
            if src and src not in seen_sources:
                seen_sources.add(src)
                sources.append(src)

        history_text = ""
        if history:
            lines = []
            for h in history[-6:]:  # เก็บแค่ 3 รอบล่าสุด
                role = "ผู้ใช้" if h["role"] == "user" else "ผู้ช่วย"
                lines.append(f"{role}: {h['content']}")
            history_text = "\n".join(lines) + "\n\n"

        prompt = PromptTemplate(
            template=(
                "คุณเป็นผู้เชี่ยวชาญด้านการปลูกข้าว เชี่ยวชาญเป็นพิเศษใน 4 พันธุ์ ได้แก่ "
                "ข้าวหอมมะลิ, ข้าว RD43, ข้าวกข 15 และข้าวปทุมธานี ตอบเป็นภาษาไทย\n"
                "หากมีข้อมูลอ้างอิงด้านล่าง ให้ใช้ข้อมูลนั้นประกอบการตอบ\n"
                "หากไม่มีข้อมูลด้านล่าง ให้บอกว่าไม่มีข้อมูลเรื่องนี้ในระบบและไม่สามารถตอบได้\n\n"
                "ข้อมูล:\n{context}\n\n"
                "{history}คำถาม: {question}\n\n"
                "คำตอบ:"
            ),
            input_variables=["context", "history", "question"],
        )
        answer = (prompt | self.llm).invoke({"context": context, "history": history_text, "question": question})
        answer = re.sub(r'\*+', '', answer).strip()

        ram_after = psutil.Process().memory_info().rss / 1024 / 1024

        return {
            "answer": answer,
            "sources": sources,
            "model_used": settings.OLLAMA_LLM_MODEL,
            "embedding_model": settings.OLLAMA_EMBEDDING_MODEL,
            "retrieval_strategy": settings.RETRIEVAL_STRATEGY,
            "chunk_size": settings.CHUNK_SIZE,
            "chunks_retrieved": len(docs),
            "response_time_ms": round((time.time() - start) * 1000),
            "ram_used_mb": round(abs(ram_after - ram_before), 2),
        }

    def generate_plan_from_rag(self, variety_id: str, variety_name: str, start_date, area_rai: float) -> str:
        query = f"แผนการปลูกและดูแลรักษาข้าว{variety_name} ขั้นตอนการดูแล ระยะการเจริญเติบโต การใส่ปุ๋ย การจัดการน้ำ"
        collection = VARIETY_COLLECTION_MAP.get(variety_id, "general")
        docs = self._search([collection, "general"], query)
        context = "\n\n".join([doc.page_content for doc in docs])

        prompt = PromptTemplate(
            template=(
                "จากข้อมูลต่อไปนี้ สร้างแผนการปลูกข้าว{variety_name} เริ่มวันที่ {start_date} พื้นที่ {area_rai} ไร่\n\n"
                "ข้อมูล:\n{context}\n\n"
                "ตอบเป็น JSON เท่านั้น ห้ามมีข้อความอื่นนอกจาก JSON ห้ามมี markdown\n"
                "ตัวอย่าง output ที่ถูกต้อง:\n"
                '{{"tasks": [{{"day": 1, "stage": "ระยะต้นกล้า", "task_name": "เตรียมดิน", "description": "ไถคราดและปรับระดับดิน"}}, {{"day": 15, "stage": "ระยะแตกกอ", "task_name": "ใส่ปุ๋ย", "description": "ปุ๋ย 16-20-0 อัตรา 25 กก./ไร่"}}]}}\n\n'
                "JSON:"
            ),
            input_variables=["variety_name", "start_date", "area_rai", "context"],
        )
        llm_zero_temp = OllamaLLM(
            model=settings.OLLAMA_LLM_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0,
        )
        chain = prompt | llm_zero_temp
        return chain.invoke({
            "variety_name": variety_name,
            "start_date": str(start_date),
            "area_rai": area_rai,
            "context": context,
        })

    def ask_question_no_rag(self, question: str) -> dict:
        start = time.time()
        ram_before = psutil.Process().memory_info().rss / 1024 / 1024

        prompt = PromptTemplate(
            template=(
                "ตอบคำถามต่อไปนี้จากความรู้ทั่วไปของคุณ\n\n"
                "คำถาม: {question}\n\n"
                "คำตอบ:"
            ),
            input_variables=["question"],
        )
        chain = prompt | self.llm
        answer = chain.invoke({"question": question})

        ram_after = psutil.Process().memory_info().rss / 1024 / 1024

        return {
            "answer": answer,
            "sources": [],
            "model_used": settings.OLLAMA_LLM_MODEL,
            "embedding_model": "",
            "retrieval_strategy": "none",
            "chunk_size": 0,
            "chunks_retrieved": 0,
            "response_time_ms": round((time.time() - start) * 1000),
            "ram_used_mb": round(abs(ram_after - ram_before), 2),
        }

    def delete_document(self, file_path: str, collection_name: str):
        file_path = os.path.abspath(file_path)
        vs = self.vectorstores.get(collection_name)
        if vs:
            vs._collection.delete(where={"source": file_path})
        if os.path.exists(file_path):
            os.remove(file_path)


rag_service = RAGService()
