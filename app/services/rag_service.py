import json
import os
import random
import re
import time

_STRIP_ASTERISKS = re.compile(r"\*+")

from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from app.core.config import settings
from app.utils.text import answer_uses_general_knowledge, normalize_question
from app.services.document_loaders import load_documents
from app.services.rag_prompts import (
    DEFAULT_PROMPT_SUGGESTIONS,
    NO_RAG_TEMPLATE,
    PROMPT_SUGGESTION_TOPICS,
    PROMPT_SUGGESTIONS_TEMPLATE,
    RAG_QA_TEMPLATE,
)


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

        key = normalize_question(content)
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
        scored_docs: list[tuple] = []
        for name in collections:
            vs = self.vectorstores.get(name)
            if vs is None:
                continue
            try:
                if vs._collection.count() == 0:
                    continue
                results = vs.similarity_search_with_relevance_scores(
                    question, k=settings.RETRIEVAL_K
                )
                for doc, score in results:
                    if score >= settings.RETRIEVAL_MIN_SCORE:
                        scored_docs.append((doc, score))
            except Exception:
                pass
        scored_docs.sort(key=lambda item: item[1], reverse=True)
        seen = set()
        unique = []
        for doc, _score in scored_docs:
            key = doc.page_content[:80]
            if key not in seen:
                seen.add(key)
                unique.append(doc)
        return unique[: settings.RETRIEVAL_K * 2]

    def ingest_document(self, file_path: str, collection_name: str) -> str:
        file_path = os.path.abspath(file_path)
        docs = load_documents(file_path)

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

        history_text = self._build_history_text(history)

        prompt = PromptTemplate(
            template=RAG_QA_TEMPLATE,
            input_variables=["context", "question", "history_text"],
        )
        raw = (prompt | self.llm).invoke(
            {"context": context, "question": question, "history_text": history_text}
        )
        input_tokens, output_tokens = _extract_token_usage(raw)
        answer = _STRIP_ASTERISKS.sub(
            "", str(raw.content) if hasattr(raw, "content") else raw
        ).strip()

        if answer_uses_general_knowledge(answer):
            docs = []

        seen_sources = set()
        sources = []
        for doc in docs:
            src = os.path.basename(doc.metadata.get("source", ""))
            if src and src not in seen_sources:
                seen_sources.add(src)
                sources.append(src)

        return {
            "answer": answer,
            "sources": sources,
            "model_used": settings.GEMINI_MODEL,
            "embedding_model": settings.GEMINI_EMBEDDING_MODEL,
            "retrieval_strategy": "relevance_threshold",
            "chunk_size": settings.CHUNK_SIZE,
            "retrieval_k": settings.RETRIEVAL_K,
            "chunks_retrieved": len(docs),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "response_time_ms": round((time.time() - start) * 1000),
        }

    def generate_prompt_suggestions(self, existing_questions: list[str] | None = None) -> list[dict]:
        topics = random.sample(
            PROMPT_SUGGESTION_TOPICS,
            k=min(random.randint(2, 3), len(PROMPT_SUGGESTION_TOPICS)),
        )
        query = " ".join(topics)
        docs = self._search(list(self.vectorstores.keys()), query)
        context = "\n\n".join([doc.page_content for doc in docs])

        existing = existing_questions or []
        existing_text = (
            "\n".join(f"- {q}" for q in existing)
            if existing
            else "(ยังไม่มีคำถามในระบบ)"
        )

        prompt = PromptTemplate(
            template=PROMPT_SUGGESTIONS_TEMPLATE,
            input_variables=["context", "existing_questions"],
        )
        raw = (prompt | self.llm).invoke(
            {"context": context, "existing_questions": existing_text}
        )
        raw = str(raw.content) if hasattr(raw, "content") else raw
        raw = raw.strip()

        try:
            match = re.search(r"\[.*\]", raw, re.DOTALL)
            if match:
                result = json.loads(match.group())
                return _normalize_prompt_suggestions(result)
        except Exception:
            pass
        return DEFAULT_PROMPT_SUGGESTIONS

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
            template=NO_RAG_TEMPLATE,
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
