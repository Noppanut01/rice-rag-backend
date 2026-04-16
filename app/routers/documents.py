import shutil
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.dependencies import get_db, require_admin
from app.models.document import Document
from app.models.variety import RiceVariety
from app.schemas.document import DocumentResponse
from app.services.rag_service import rag_service

router = APIRouter(prefix="/documents", tags=["documents"])


def _doc_to_response(doc: Document) -> DocumentResponse:
    return DocumentResponse(
        id=str(doc.id),
        filename=str(doc.filename),
        file_type=Path(str(doc.filename)).suffix.lstrip(".").lower(),
        chroma_collection=str(doc.chroma_collection),
        created_at=str(doc.created_at),
    )


@router.get("/collections")
def list_collections(db: Session = Depends(get_db)):
    varieties = db.query(RiceVariety).filter(RiceVariety.is_active == True).all()
    result = [{"value": v.collection_name, "label": v.name} for v in varieties]
    result.append({"value": "general", "label": "ทั่วไป"})
    return result


@router.get("/", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    return [_doc_to_response(doc) for doc in db.query(Document).all()]


@router.post("/upload", response_model=list[DocumentResponse])
def upload(
    files: list[UploadFile] = File(...),
    collection: str = Form("general"),
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    valid_collections = {v.collection_name for v in db.query(RiceVariety).all()} | {"general"}
    if collection not in valid_collections:
        raise HTTPException(status_code=400, detail=f"ไม่พบ collection '{collection}'")

    results = []
    for file in files:
        if not file.filename or not file.filename.endswith((".pdf", ".txt", ".docx")):
            raise HTTPException(status_code=400, detail="รองรับแค่ .pdf .txt .docx")

        collection_dir = Path(settings.UPLOAD_DIR) / collection
        collection_dir.mkdir(parents=True, exist_ok=True)
        file_path = collection_dir / file.filename
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

        results.append(_doc_to_response(doc))

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
    inline_types = {".pdf", ".txt"}
    if suffix in inline_types:
        disposition_header = "inline"
    else:
        encoded_name = quote(str(document.filename), safe="")
        disposition_header = f"attachment; filename*=UTF-8''{encoded_name}"
    return FileResponse(
        path=str(file_path),
        media_type=media_types.get(suffix, "application/octet-stream"),
        headers={"Content-Disposition": disposition_header},
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
