from pydantic import BaseModel

from app.models.variety import RiceVariety


class RiceVarietyCreate(BaseModel):
    name: str
    collection_name: str
    harvest_age_days: int
    is_photoperiod_sensitive: bool = False
    supported_methods: list[str] = ["transplant", "broadcast"]
    tillering_day: int
    panicle_initiation_day: int
    heading_day: int
    fert1_rate: float | None = None
    fert2_rate: float | None = None
    fert2_formula: str | None = None
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
    fert1_rate: float | None
    fert2_rate: float | None
    fert2_formula: str | None
    fert1_note: str | None
    fert2_note: str | None


def variety_to_response(variety: RiceVariety) -> RiceVarietyResponse:
    return RiceVarietyResponse(
        id=str(variety.id),
        name=str(variety.name),
        collection_name=str(variety.collection_name),
        harvest_age_days=int(variety.harvest_age_days),
        is_photoperiod_sensitive=bool(variety.is_photoperiod_sensitive),
        supported_methods=list(variety.supported_methods),
        description=str(variety.description) if variety.description else None,
        reference_url=str(variety.reference_url) if variety.reference_url else None,
        tillering_day=int(variety.tillering_day) if variety.tillering_day is not None else None,
        panicle_initiation_day=int(variety.panicle_initiation_day)
        if variety.panicle_initiation_day is not None
        else None,
        heading_day=int(variety.heading_day) if variety.heading_day is not None else None,
        fert1_rate=float(variety.fert1_rate) if variety.fert1_rate is not None else None,
        fert2_rate=float(variety.fert2_rate) if variety.fert2_rate is not None else None,
        fert2_formula=str(variety.fert2_formula) if variety.fert2_formula else None,
        fert1_note=str(variety.fert1_note) if variety.fert1_note else None,
        fert2_note=str(variety.fert2_note) if variety.fert2_note else None,
    )
