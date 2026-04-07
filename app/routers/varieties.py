from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_admin
from app.models.variety import RiceVariety
from app.services.rag_service import rag_service

router = APIRouter(prefix="/varieties", tags=["varieties"])


class RiceVarietyCreate(BaseModel):
    name: str
    collection_name: str
    harvest_age_days: int
    is_photoperiod_sensitive: bool = False
    supported_methods: list[str] = ["transplant", "broadcast"]
    description: str | None = None
    reference_url: str | None = None
    tillering_day: int | None = None
    panicle_initiation_day: int | None = None
    heading_day: int | None = None
    fert1_rate_min: float | None = None
    fert1_rate_max: float | None = None
    fert2_rate_min: float | None = None
    fert2_rate_max: float | None = None
    fert1_formula: str | None = None
    fert2_formula: str | None = None
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
    fert1_rate_min: float | None = None
    fert1_rate_max: float | None = None
    fert2_rate_min: float | None = None
    fert2_rate_max: float | None = None
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
    supported_methods: list[str]
    description: str | None
    reference_url: str | None
    tillering_day: int | None
    panicle_initiation_day: int | None
    heading_day: int | None
    fert1_rate_min: float | None
    fert1_rate_max: float | None
    fert2_rate_min: float | None
    fert2_rate_max: float | None
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
        supported_methods=list(v.supported_methods),
        description=str(v.description) if v.description else None,
        reference_url=str(v.reference_url) if v.reference_url else None,
        tillering_day=int(v.tillering_day) if v.tillering_day is not None else None,
        panicle_initiation_day=int(v.panicle_initiation_day) if v.panicle_initiation_day is not None else None,
        heading_day=int(v.heading_day) if v.heading_day is not None else None,
        fert1_rate_min=float(v.fert1_rate_min) if v.fert1_rate_min is not None else None,
        fert1_rate_max=float(v.fert1_rate_max) if v.fert1_rate_max is not None else None,
        fert2_rate_min=float(v.fert2_rate_min) if v.fert2_rate_min is not None else None,
        fert2_rate_max=float(v.fert2_rate_max) if v.fert2_rate_max is not None else None,
        fert1_formula=str(v.fert1_formula) if v.fert1_formula else None,
        fert2_formula=str(v.fert2_formula) if v.fert2_formula else None,
        fert1_note=str(v.fert1_note) if v.fert1_note else None,
        fert2_note=str(v.fert2_note) if v.fert2_note else None,
    )


@router.get("/", response_model=list[RiceVarietyResponse])
def list_varieties(db: Session = Depends(get_db)):
    return [_to_response(v) for v in db.query(RiceVariety).all()]


@router.post("/", response_model=RiceVarietyResponse)
def create_variety(body: RiceVarietyCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    if db.query(RiceVariety).filter(RiceVariety.collection_name == body.collection_name).first():
        raise HTTPException(status_code=400, detail="collection_name นี้มีอยู่แล้ว")

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
        fert1_rate_min=body.fert1_rate_min,
        fert1_rate_max=body.fert1_rate_max,
        fert2_rate_min=body.fert2_rate_min,
        fert2_rate_max=body.fert2_rate_max,
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

    fields = [
        "name", "harvest_age_days", "is_photoperiod_sensitive", "supported_methods",
        "description", "reference_url", "tillering_day", "panicle_initiation_day",
        "heading_day", "fert1_rate_min", "fert1_rate_max", "fert2_rate_min", "fert2_rate_max",
        "fert1_formula", "fert2_formula", "fert1_note", "fert2_note",
    ]
    for field in fields:
        val = getattr(body, field)
        if val is not None:
            setattr(variety, field, val)

    db.commit()
    db.refresh(variety)
    return _to_response(variety)


@router.delete("/{variety_id}", status_code=204)
def delete_variety(variety_id: str, db: Session = Depends(get_db), _=Depends(require_admin)):
    variety = db.query(RiceVariety).filter(RiceVariety.id == variety_id).first()
    if not variety:
        raise HTTPException(status_code=404, detail="ไม่พบพันธุ์ข้าว")
    db.delete(variety)
    db.commit()
