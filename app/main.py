from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database import Base, SessionLocal, engine

Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

# noqa: F401 — import models so Base knows all tables before create_all
from app.models import chat, document, plan, prompt, user, variety  # noqa: F401

app = FastAPI(title="Rice Farming RAG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

from app.routers import admin, auth, documents, plans, prompts, varieties  # noqa: E402
from app.routers import chat as chat_router  # noqa: E402
from app.services.rag_service import rag_service  # noqa: E402

app.include_router(auth.router)
app.include_router(chat_router.router)
app.include_router(documents.router)
app.include_router(plans.router)
app.include_router(prompts.router)
app.include_router(varieties.router)
app.include_router(admin.router)

SEED_VARIETIES = [
    {
        "name": "ข้าวขาวดอกมะลิ 105",
        "collection_name": "jasmine",
        "harvest_age_days": 120,
        "is_photoperiod_sensitive": True,
        "supported_methods": ["transplant", "broadcast"],
        "description": "ข้าวจ้าวไวต่อช่วงแสง กลิ่นหอม เมล็ดเรียวยาว ปลูกได้เฉพาะนาปี",
        "reference_url": "https://www.ricethailand.go.th",
    },
    {
        "name": "ข้าว กข43",
        "collection_name": "rd43",
        "harvest_age_days": 95,
        "is_photoperiod_sensitive": False,
        "supported_methods": ["transplant", "broadcast", "throw"],
        "description": "ข้าวเจ้าไม่ไวแสง ดัชนีน้ำตาลต่ำ อายุสั้น ปลูกได้ตลอดปี",
        "reference_url": "https://www.ricethailand.go.th",
    },
    {
        "name": "ข้าว กข15",
        "collection_name": "kk15",
        "harvest_age_days": 100,
        "is_photoperiod_sensitive": True,
        "supported_methods": ["transplant", "broadcast"],
        "description": "ข้าวหอมมะลิไวแสง เก็บเกี่ยวเร็วกว่าหอมมะลิ 105 ประมาณ 20 วัน",
        "reference_url": "https://www.ricethailand.go.th",
    },
    {
        "name": "ข้าวปทุมธานี 1",
        "collection_name": "pathumthani",
        "harvest_age_days": 120,
        "is_photoperiod_sensitive": False,
        "supported_methods": ["transplant", "broadcast", "throw"],
        "description": "ข้าวเจ้าหอมไม่ไวแสง ปลูกได้ทั้งนาปีและนาปรัง",
        "reference_url": "https://www.ricethailand.go.th",
    },
]


@app.on_event("startup")
def startup():
    from app.models.variety import RiceVariety
    db = SessionLocal()
    try:
        if db.query(RiceVariety).count() == 0:
            for v in SEED_VARIETIES:
                db.add(RiceVariety(**v))
            db.commit()

        varieties = db.query(RiceVariety).all()
        collection_names = [v.collection_name for v in varieties] + ["general"]
        rag_service.load_collections(list(set(collection_names)))
    finally:
        db.close()
