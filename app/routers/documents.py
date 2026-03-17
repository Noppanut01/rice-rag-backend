import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.dependencies import get_db, require_admin
from app.models.document import Document
from app.schemas.document import DocumentResponse
from app.services.rag_service import COLLECTIONS, rag_service

router = APIRouter(prefix="/documents", tags=["documents"])

COLLECTION_LABELS = {
    "jasmine": "ข้าวหอมมะลิ",
    "rd43": "ข้าว RD43",
    "kk15": "ข้าวกข 15",
    "pathumthani": "ข้าวปทุมธานี",
    "general": "ทั่วไป",
}


@router.get("/collections")
def list_collections(db: Session = Depends(get_db)):
    rows = db.query(Document.chroma_collection).distinct().all()
    return [
        {"value": row[0], "label": COLLECTION_LABELS.get(row[0], row[0])}
        for row in rows
    ]


@router.get("/", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    return [
        DocumentResponse(
            id=str(doc.id),
            filename=str(doc.filename),
            file_type=Path(str(doc.filename)).suffix.lstrip(".").lower(),
            chroma_collection=str(doc.chroma_collection),
            created_at=str(doc.created_at),
        )
        for doc in db.query(Document).all()
    ]


@router.post("/upload", response_model=list[DocumentResponse])
def upload(
    files: list[UploadFile] = File(...),
    collection: str = Form("general"),
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    if collection not in COLLECTIONS:
        raise HTTPException(status_code=400, detail=f"collection ต้องเป็นหนึ่งใน {COLLECTIONS}")

    results = []
    for file in files:
        if not file.filename or not file.filename.endswith((".pdf", ".txt", ".docx")):
            raise HTTPException(status_code=400, detail="รองรับแค่ .pdf .txt .docx")

        file_path = Path(settings.UPLOAD_DIR) / file.filename
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        rag_service.ingest_document(file_path=str(file_path), collection_name=collection)

        doc = Document(
            filename=file.filename,
            file_path=str(file_path),
            chroma_collection=collection,
            uploaded_by=current_user.id,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        results.append(
            DocumentResponse(
                id=str(doc.id),
                filename=str(doc.filename),
                file_type=Path(str(doc.filename)).suffix.lstrip(".").lower(),
                chroma_collection=str(doc.chroma_collection),
                created_at=str(doc.created_at),
            )
        )

    return results


@router.get("/{id}/file")
def get_file(id: str, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == id).first()
    if not document:
        raise HTTPException(status_code=404, detail="ไม่พบเอกสาร")
    file_path = Path(str(document.file_path))
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="ไม่พบไฟล์ในระบบ")
    suffix = file_path.suffix.lower()
    media_types = {
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    media_type = media_types.get(suffix, "application/octet-stream")
    return FileResponse(
        path=str(file_path),
        filename=str(document.filename),
        media_type=media_type,
    )


@router.delete("/{id}", status_code=204)
def delete(id: str, db: Session = Depends(get_db), _=Depends(require_admin)):
    document = db.query(Document).filter(Document.id == id).first()
    if not document:
        raise HTTPException(status_code=404, detail="ไม่พบเอกสาร")
    rag_service.delete_document(str(document.file_path), str(document.chroma_collection))
    db.delete(document)
    db.commit()
    return Response(status_code=204)
