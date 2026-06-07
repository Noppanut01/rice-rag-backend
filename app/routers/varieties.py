import shutil
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.dependencies import get_db, require_admin
from app.models.document import Document
from app.models.variety import RiceVariety
from app.schemas.variety import (
    RiceVarietyCreate,
    RiceVarietyResponse,
    RiceVarietyUpdate,
    variety_to_response,
)
from app.services.rag_service import rag_service
from app.utils.http_errors import bad_request, not_found

router = APIRouter(prefix="/varieties", tags=["varieties"])


def _validate_growth_stages(
    harvest_age_days: int | None,
    tillering_day: int | None,
    panicle_initiation_day: int | None,
    heading_day: int | None,
) -> None:
    if None in (harvest_age_days, tillering_day, panicle_initiation_day, heading_day):
        raise bad_request(
            "กรุณากรอกอายุเก็บเกี่ยว วันแตกกอ วันกำเนิดช่อดอก และวันออกรวงให้ครบ",
        )
    if not (0 <= tillering_day < panicle_initiation_day < heading_day < harvest_age_days):
        raise bad_request(
            "ระยะการเจริญเติบโตต้องเรียงลำดับ: แตกกอ < กำเนิดช่อดอก < ออกรวง < อายุเก็บเกี่ยว",
        )


def _validate_fertilizer(
    fert1_rate: float | None,
    fert2_rate: float | None,
    fert2_formula: str | None,
) -> None:
    if fert1_rate is None or fert1_rate < 0:
        raise bad_request("กรุณากรอกอัตราปุ๋ยช่วงแตกกอให้ถูกต้อง")
    if fert2_rate is None or fert2_rate < 0:
        raise bad_request("กรุณากรอกอัตราปุ๋ยช่วงกำเนิดช่อดอกให้ถูกต้อง")
    if not fert2_formula or not fert2_formula.strip():
        raise bad_request("กรุณากรอกสูตรปุ๋ยช่วงกำเนิดช่อดอก")


@router.get("/", response_model=list[RiceVarietyResponse])
def list_varieties(db: Session = Depends(get_db)):
    return [variety_to_response(v) for v in db.query(RiceVariety).all()]


@router.post("/", response_model=RiceVarietyResponse)
def create_variety(body: RiceVarietyCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    if " " in body.collection_name or not body.collection_name == body.collection_name.lower():
        raise bad_request("collection_name ต้องเป็นตัวพิมพ์เล็กและห้ามมีช่องว่าง")
    if db.query(RiceVariety).filter(RiceVariety.collection_name == body.collection_name).first():
        raise bad_request("collection_name นี้มีอยู่แล้ว")
    _validate_growth_stages(
        body.harvest_age_days,
        body.tillering_day,
        body.panicle_initiation_day,
        body.heading_day,
    )
    _validate_fertilizer(body.fert1_rate, body.fert2_rate, body.fert2_formula)

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
        fert1_formula="",
        fert2_formula=body.fert2_formula.strip(),
        fert1_note=body.fert1_note,
        fert2_note=body.fert2_note,
    )
    db.add(variety)
    db.commit()
    db.refresh(variety)

    rag_service.load_collections([body.collection_name])

    return variety_to_response(variety)


@router.put("/{variety_id}", response_model=RiceVarietyResponse)
def update_variety(variety_id: str, body: RiceVarietyUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    variety = db.query(RiceVariety).filter(RiceVariety.id == variety_id).first()
    if not variety:
        raise not_found("ไม่พบพันธุ์ข้าว")

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
    fert1_rate = updates.get("fert1_rate", variety.fert1_rate)
    fert2_rate = updates.get("fert2_rate", variety.fert2_rate)
    fert2_formula = updates.get("fert2_formula", variety.fert2_formula)
    _validate_fertilizer(
        float(fert1_rate) if fert1_rate is not None else None,
        float(fert2_rate) if fert2_rate is not None else None,
        str(fert2_formula) if fert2_formula is not None else None,
    )
    if "fert2_formula" in updates and isinstance(updates["fert2_formula"], str):
        updates["fert2_formula"] = updates["fert2_formula"].strip()

    for field, val in updates.items():
        setattr(variety, field, val)

    db.commit()
    db.refresh(variety)
    return variety_to_response(variety)


@router.get("/{variety_id}/stats")
def get_variety_stats(variety_id: str, db: Session = Depends(get_db), _=Depends(require_admin)):
    variety = db.query(RiceVariety).filter(RiceVariety.id == variety_id).first()
    if not variety:
        raise not_found("ไม่พบพันธุ์ข้าว")
    doc_count = db.query(Document).filter(Document.chroma_collection == variety.collection_name).count()
    return {"doc_count": doc_count, "collection_name": str(variety.collection_name)}


@router.delete("/{variety_id}")
def delete_variety(variety_id: str, db: Session = Depends(get_db), _=Depends(require_admin)):
    variety = db.query(RiceVariety).filter(RiceVariety.id == variety_id).first()
    if not variety:
        raise not_found("ไม่พบพันธุ์ข้าว")

    docs = db.query(Document).filter(Document.chroma_collection == variety.collection_name).all()
    for doc in docs:
        try:
            Path(str(doc.file_path)).unlink(missing_ok=True)
        except Exception:
            pass
        rag_service.delete_document(str(doc.file_path), str(variety.collection_name))
        db.delete(doc)

    collection_dir = Path(settings.UPLOAD_DIR) / str(variety.collection_name)
    if collection_dir.exists():
        shutil.rmtree(collection_dir, ignore_errors=True)

    db.delete(variety)
    db.commit()
    return {"detail": f"ลบพันธุ์ข้าว '{variety.name}' และเอกสารที่เกี่ยวข้องทั้งหมดเรียบร้อย"}
