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

@app.on_event("startup")
def startup():
    from app.models.variety import RiceVariety
    db = SessionLocal()
    try:
        varieties = db.query(RiceVariety).all()
        collection_names = [v.collection_name for v in varieties] + ["general"]
        rag_service.load_collections(list(set(collection_names)))
    finally:
        db.close()
