import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, JSON, String, func

from app.database import Base


class RiceVariety(Base):
    __tablename__ = "rice_varieties"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    collection_name = Column(String, nullable=False, unique=True)
    harvest_age_days = Column(Integer, nullable=False)
    is_photoperiod_sensitive = Column(Boolean, default=False)
    supported_methods = Column(JSON, nullable=False, default=["transplant", "broadcast"])
    description = Column(String, nullable=True)
    reference_url = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # ระยะการเจริญเติบโต (วันนับจากวันปลูก)
    tillering_day = Column(Integer, nullable=False)
    panicle_initiation_day = Column(Integer, nullable=False)
    heading_day = Column(Integer, nullable=True)
    # Legacy column — runtime ไม่ filter ตาม is_active แล้ว (เก็บไว้หลีกเลี่ยง migration)
    is_active = Column(Boolean, default=True, nullable=False)

    # ปุ๋ย — อัตรา (กก./ไร่) สูตรและหมายเหตุ
    fert1_rate = Column(Float, nullable=False)
    fert2_rate = Column(Float, nullable=False)
    fert1_formula = Column(String, nullable=False)
    fert2_formula = Column(String, nullable=False)
    fert1_note = Column(String, nullable=True)
    fert2_note = Column(String, nullable=True)
