import time

import psutil
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_ollama import OllamaEmbeddings, OllamaLLM

from app.core.config import settings


class RAGService:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(
            model=settings.OLLAMA_EMBEDDING_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
        )
        self.vectorstore = Chroma(
            collection_name="rice_knowledge",
            embedding_function=self.embeddings,
            persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
        )
        self.llm = OllamaLLM(
            model=settings.OLLAMA_LLM_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=settings.LLM_TEMPERATURE,
        )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

    def ingest_document(self, file_path: str, collection_name: str) -> str:
        # เลือก loader ตาม extension
        if file_path.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        elif file_path.endswith(".docx"):
            loader = Docx2txtLoader(file_path)
        else:
            loader = TextLoader(file_path, encoding="utf-8")

        docs = loader.load()
        chunks = self.splitter.split_documents(docs)

        # บันทึกลง ChromaDB แยก collection ต่อไฟล์
        Chroma.from_documents(
            chunks,
            embedding=self.embeddings,
            collection_name=collection_name,
            persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
        )

        return collection_name

    def ask_question(self, question: str) -> dict:
        start = time.time()
        ram_before = psutil.Process().memory_info().rss / 1024 / 1024

        # Retrieve chunks
        if settings.RETRIEVAL_STRATEGY == "mmr":
            docs = self.vectorstore.max_marginal_relevance_search(
                question, k=settings.RETRIEVAL_K, fetch_k=10
            )
        else:
            docs = self.vectorstore.similarity_search(question, k=settings.RETRIEVAL_K)

        # Build context
        context = "\n\n".join([doc.page_content for doc in docs])
        sources = [doc.metadata.get("source", "") for doc in docs]

        # Prompt
        prompt = PromptTemplate(
            template=(
                "ใช้ข้อมูลต่อไปนี้เพื่อตอบคำถาม\n\n"
                "ข้อมูล:\n{context}\n\n"
                "คำถาม: {question}\n\n"
                "คำตอบ:"
            ),
            input_variables=["context", "question"],
        )

        chain = prompt | self.llm
        answer = chain.invoke({"context": context, "question": question})

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
            "ram_used_mb": round(ram_after - ram_before, 2),
        }

    def delete_collection(self, collection_name: str):
        self.vectorstore._client.delete_collection(collection_name)


# TODO: เพิ่ม method ต่อไปนี้เมื่อต้องการ
# - ask_question_with_collection(question, collection_name) — ถามเฉพาะเอกสารนั้น
# - search_all_collections(question) — ค้นหาข้ามทุก collection แล้วรวมผล (แบบของเก่า)

rag_service = RAGService()
