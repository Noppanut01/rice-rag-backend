from sqlalchemy.orm import Session

from app.models.variety import RiceVariety
from app.schemas.plan import PlanRequest, PlanUpdateRequest
from app.utils.http_errors import bad_request, not_found

VALID_SOIL_TYPES = frozenset({"clay", "loam", "sandy"})


def validate_area_rai(area_rai: float) -> None:
    if area_rai <= 0:
        raise bad_request("พื้นที่ต้องมากกว่า 0")


def validate_soil_type(soil_type: str) -> None:
    if soil_type not in VALID_SOIL_TYPES:
        raise bad_request("ประเภทดินไม่ถูกต้อง")


def get_variety_or_404(db: Session, variety_id: str) -> RiceVariety:
    variety = db.query(RiceVariety).filter(RiceVariety.id == variety_id).first()
    if not variety:
        raise not_found("ไม่พบพันธุ์ข้าว")
    return variety


def validate_planting_method(variety: RiceVariety, planting_method: str) -> None:
    if planting_method not in variety.supported_methods:
        raise bad_request(f"พันธุ์ {variety.name} ไม่รองรับวิธีปลูก '{planting_method}'")


def validate_create_plan(body: PlanRequest, db: Session) -> RiceVariety:
    validate_area_rai(body.area_rai)
    variety = get_variety_or_404(db, body.variety_id)
    validate_planting_method(variety, body.planting_method)
    return variety


def validate_update_plan(body: PlanUpdateRequest) -> None:
    if body.area_rai is not None:
        validate_area_rai(body.area_rai)
    if body.soil_type is not None:
        validate_soil_type(body.soil_type)
