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
    tillering_day = Column(Integer, nullable=True)
    panicle_initiation_day = Column(Integer, nullable=True)
    heading_day = Column(Integer, nullable=True)
    # วันออกดอกตามปฏิทิน รูปแบบ "MM-DD" เช่น "11-20" = 20 พ.ย. (ใช้กับข้าวไวแสงเท่านั้น)
    heading_calendar = Column(String, nullable=True)

    # ปุ๋ย — เก็บช่วง min-max (กก./ไร่) สูตรและหมายเหตุ
    fert1_rate_min = Column(Float, nullable=True)
    fert1_rate_max = Column(Float, nullable=True)
    fert2_rate_min = Column(Float, nullable=True)
    fert2_rate_max = Column(Float, nullable=True)
    fert1_formula = Column(String, nullable=True)   # เช่น 16-20-0 (ถ้าไม่ระบุจะใช้ตาม soil_type)
    fert2_formula = Column(String, nullable=True)
    fert1_note = Column(String, nullable=True)
    fert2_note = Column(String, nullable=True)
