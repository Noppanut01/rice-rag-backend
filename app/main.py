from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine

# Import models เพื่อให้ Base รู้จัก tables ทั้งหมดก่อน create_all
from app.models import chat, document, plan, user  # noqa: F401

# TODO: import models/prompt เมื่อสร้างแล้ว

app = FastAPI(title="Rice Farming RAG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# สร้าง tables ทั้งหมดตอน startup
Base.metadata.create_all(bind=engine)

# Include routers (uncomment ทีละตัวเมื่อเขียนเสร็จ)
# from app.routers import chat as chat_router
from app.routers import auth, documents

# from app.routers import plans
# from app.routers import prompts
# from app.routers import admin

app.include_router(auth.router)
# app.include_router(chat_router.router)
# app.include_router(documents.router)
# app.include_router(plans.router)
# app.include_router(prompts.router)
# app.include_router(admin.router)
