import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.dependencies import get_db, require_admin
from app.models.document import Document
from app.models.variety import RiceVariety
from app.services.rag_service import rag_service

router = APIRouter(prefix="/varieties", tags=["varieties"])


class RiceVarietyCreate(BaseModel):
    name: str
    collection_name: str
    harvest_age_days: int
    is_photoperiod_sensitive: bool = False
    supported_methods: list[str] = ["transplant", "broadcast"]
    tillering_day: int
    panicle_initiation_day: int
    heading_day: int
    fert1_rate: float
    fert2_rate: float
    fert1_formula: str
    fert2_formula: str
    description: str | None = None
    reference_url: str | None = None
    fert1_note: str | None = None
    fert2_note: str | None = None


class RiceVarietyUpdate(BaseModel):
    name: str | None = None
    harvest_age_days: int | None = None
    is_photoperiod_sensitive: bool | None = None
    supported_methods: list[str] | None = None
    description: str | None = None
    reference_url: str | None = None
    tillering_day: int | None = None
    panicle_initiation_day: int | None = None
    heading_day: int | None = None
    fert1_rate: float | None = None
    fert2_rate: float | None = None
    fert1_formula: str | None = None
    fert2_formula: str | None = None
    fert1_note: str | None = None
    fert2_note: str | None = None


class RiceVarietyResponse(BaseModel):
    id: str
    name: str
    collection_name: str
    harvest_age_days: int
    is_photoperiod_sensitive: bool
    is_active: bool
    supported_methods: list[str]
    description: str | None
    reference_url: str | None
    tillering_day: int | None
    panicle_initiation_day: int | None
    heading_day: int | None
    fert1_rate: float | None
    fert2_rate: float | None
    fert1_formula: str | None
    fert2_formula: str | None
    fert1_note: str | None
    fert2_note: str | None


def _to_response(v: RiceVariety) -> RiceVarietyResponse:
    return RiceVarietyResponse(
        id=str(v.id),
        name=str(v.name),
        collection_name=str(v.collection_name),
        harvest_age_days=int(v.harvest_age_days),
        is_photoperiod_sensitive=bool(v.is_photoperiod_sensitive),
        is_active=bool(v.is_active),
        supported_methods=list(v.supported_methods),
        description=str(v.description) if v.description else None,
        reference_url=str(v.reference_url) if v.reference_url else None,
        tillering_day=int(v.tillering_day) if v.tillering_day is not None else None,
        panicle_initiation_day=int(v.panicle_initiation_day) if v.panicle_initiation_day is not None else None,
        heading_day=int(v.heading_day) if v.heading_day is not None else None,
        fert1_rate=float(v.fert1_rate) if v.fert1_rate is not None else None,
        fert2_rate=float(v.fert2_rate) if v.fert2_rate is not None else None,
        fert1_formula=str(v.fert1_formula) if v.fert1_formula else None,
        fert2_formula=str(v.fert2_formula) if v.fert2_formula else None,
        fert1_note=str(v.fert1_note) if v.fert1_note else None,
        fert2_note=str(v.fert2_note) if v.fert2_note else None,
    )


def _validate_growth_stages(
    harvest_age_days: int | None,
    tillering_day: int | None,
    panicle_initiation_day: int | None,
    heading_day: int | None,
) -> None:
    if None in (harvest_age_days, tillering_day, panicle_initiation_day, heading_day):
        raise HTTPException(
            status_code=400,
            detail="กรุณากรอกอายุเก็บเกี่ยว วันแตกกอ วันกำเนิดช่อดอก และวันออกรวงให้ครบ",
        )
    if not (0 <= tillering_day < panicle_initiation_day < heading_day < harvest_age_days):
        raise HTTPException(
            status_code=400,
            detail="ระยะการเจริญเติบโตต้องเรียงลำดับ: แตกกอ < กำเนิดช่อดอก < ออกรวง < อายุเก็บเกี่ยว",
        )


@router.get("/", response_model=list[RiceVarietyResponse])
def list_varieties(db: Session = Depends(get_db)):
    return [_to_response(v) for v in db.query(RiceVariety).filter(RiceVariety.is_active == True).all()]


@router.post("/", response_model=RiceVarietyResponse)
def create_variety(body: RiceVarietyCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    if " " in body.collection_name or not body.collection_name == body.collection_name.lower():
        raise HTTPException(status_code=400, detail="collection_name ต้องเป็นตัวพิมพ์เล็กและห้ามมีช่องว่าง")
    if db.query(RiceVariety).filter(RiceVariety.collection_name == body.collection_name).first():
        raise HTTPException(status_code=400, detail="collection_name นี้มีอยู่แล้ว")
    _validate_growth_stages(
        body.harvest_age_days,
        body.tillering_day,
        body.panicle_initiation_day,
        body.heading_day,
    )

    variety = RiceVariety(
        name=body.name,
        collection_name=body.collection_name,
        harvest_age_days=body.harvest_age_days,
        is_photoperiod_sensitive=body.is_photoperiod_sensitive,
        supported_methods=body.supported_methods,
        description=body.description,
        reference_url=body.reference_url,
        tillering_day=body.tillering_day,
        panicle_initiation_day=body.panicle_initiation_day,
        heading_day=body.heading_day,
        fert1_rate=body.fert1_rate,
        fert2_rate=body.fert2_rate,
        fert1_formula=body.fert1_formula,
        fert2_formula=body.fert2_formula,
        fert1_note=body.fert1_note,
        fert2_note=body.fert2_note,
    )
    db.add(variety)
    db.commit()
    db.refresh(variety)

    rag_service.load_collections([body.collection_name])

    return _to_response(variety)


@router.put("/{variety_id}", response_model=RiceVarietyResponse)
def update_variety(variety_id: str, body: RiceVarietyUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    variety = db.query(RiceVariety).filter(RiceVariety.id == variety_id).first()
    if not variety:
        raise HTTPException(status_code=404, detail="ไม่พบพันธุ์ข้าว")

    updates = body.model_dump(exclude_unset=True)
    harvest_age_days = updates.get("harvest_age_days", variety.harvest_age_days)
    tillering_day = updates.get("tillering_day", variety.tillering_day)
    panicle_initiation_day = updates.get(
        "panicle_initiation_day",
        variety.panicle_initiation_day,
    )
    heading_day = updates.get("heading_day", variety.heading_day)
    _validate_growth_stages(
        int(harvest_age_days) if harvest_age_days is not None else None,
        int(tillering_day) if tillering_day is not None else None,
        int(panicle_initiation_day) if panicle_initiation_day is not None else None,
        int(heading_day) if heading_day is not None else None,
    )

    for field, val in updates.items():
        setattr(variety, field, val)

    db.commit()
    db.refresh(variety)
    return _to_response(variety)


@router.get("/{variety_id}/stats")
def get_variety_stats(variety_id: str, db: Session = Depends(get_db), _=Depends(require_admin)):
    variety = db.query(RiceVariety).filter(RiceVariety.id == variety_id).first()
    if not variety:
        raise HTTPException(status_code=404, detail="ไม่พบพันธุ์ข้าว")
    doc_count = db.query(Document).filter(Document.chroma_collection == variety.collection_name).count()
    return {"doc_count": doc_count, "collection_name": str(variety.collection_name)}


@router.delete("/{variety_id}")
def delete_variety(variety_id: str, db: Session = Depends(get_db), _=Depends(require_admin)):
    variety = db.query(RiceVariety).filter(RiceVariety.id == variety_id).first()
    if not variety:
        raise HTTPException(status_code=404, detail="ไม่พบพันธุ์ข้าว")

    # ลบไฟล์และ documents ที่ผูกกับ collection นี้
    docs = db.query(Document).filter(Document.chroma_collection == variety.collection_name).all()
    for doc in docs:
        try:
            Path(str(doc.file_path)).unlink(missing_ok=True)
        except Exception:
            pass
        rag_service.delete_document(str(doc.file_path), str(variety.collection_name))
        db.delete(doc)

    # ลบโฟลเดอร์ uploads/{collection} ถ้าว่างแล้ว
    collection_dir = Path(settings.UPLOAD_DIR) / str(variety.collection_name)
    if collection_dir.exists():
        shutil.rmtree(collection_dir, ignore_errors=True)

    db.delete(variety)
    db.commit()
    return {"detail": f"ลบพันธุ์ข้าว '{variety.name}' และเอกสารที่เกี่ยวข้องทั้งหมดเรียบร้อย"}
