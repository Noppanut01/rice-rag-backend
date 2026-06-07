from langchain_community.document_loaders import Docx2txtLoader, PyMuPDFLoader, TextLoader
from langchain_core.documents import Document


def load_pdf_documents(file_path: str) -> list[Document]:
    docs = PyMuPDFLoader(file_path).load()
    for doc in docs:
        doc.metadata["extraction_method"] = "pymupdf"
    return docs


def load_documents(file_path: str) -> list[Document]:
    if file_path.endswith(".pdf"):
        return load_pdf_documents(file_path)
    if file_path.endswith(".docx"):
        return Docx2txtLoader(file_path).load()
    return TextLoader(file_path, encoding="utf-8").load()
