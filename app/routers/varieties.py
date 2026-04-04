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


class RiceVarietyResponse(BaseModel):
    id: str
    name: str
    collection_name: str
    harvest_age_days: int
    is_photoperiod_sensitive: bool
    supported_methods: list[str]
    description: str | None
    reference_url: str | None


@router.get("/", response_model=list[RiceVarietyResponse])
def list_varieties(db: Session = Depends(get_db)):
    return [
        RiceVarietyResponse(
            id=str(v.id),
            name=str(v.name),
            collection_name=str(v.collection_name),
            harvest_age_days=int(v.harvest_age_days),
            is_photoperiod_sensitive=bool(v.is_photoperiod_sensitive),
            supported_methods=list(v.supported_methods),
            description=str(v.description) if v.description else None,
            reference_url=str(v.reference_url) if v.reference_url else None,
        )
        for v in db.query(RiceVariety).all()
    ]


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
    )
    db.add(variety)
    db.commit()
    db.refresh(variety)

    rag_service.load_collections([body.collection_name])

    return RiceVarietyResponse(
        id=str(variety.id),
        name=str(variety.name),
        collection_name=str(variety.collection_name),
        harvest_age_days=int(variety.harvest_age_days),
        is_photoperiod_sensitive=bool(variety.is_photoperiod_sensitive),
        supported_methods=list(variety.supported_methods),
        description=str(variety.description) if variety.description else None,
        reference_url=str(variety.reference_url) if variety.reference_url else None,
    )


@router.delete("/{variety_id}", status_code=204)
def delete_variety(variety_id: str, db: Session = Depends(get_db), _=Depends(require_admin)):
    variety = db.query(RiceVariety).filter(RiceVariety.id == variety_id).first()
    if not variety:
        raise HTTPException(status_code=404, detail="ไม่พบพันธุ์ข้าว")
    db.delete(variety)
    db.commit()
