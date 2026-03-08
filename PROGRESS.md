# Progress — Rice Farming RAG Backend

> ✅ = เขียน code แล้ว | ❌ = แค่ comment stub | ➖ = ตัดออก

---

## Phase 1 — Foundation

- [x] `app/core/config.py` — BaseSettings จาก .env
- [x] `app/database.py` — PostgreSQL + SessionLocal
- [x] `app/core/security.py` — bcrypt + JWT
- [x] `app/dependencies.py` — get_db, get_current_user, require_admin
- [x] `app/models/user.py` — UUID, username, hashed_password, role
- [x] `app/models/document.py` — UUID, filename, file_path, chroma_collection, uploaded_by
- [x] `app/models/chat.py` — UUID, question, answer, sources, metrics
- [x] `app/models/plan.py` — UUID, variety_name, start_date, area_rai, plot_name, metrics
- [x] `app/main.py` — FastAPI app, CORS, routers, create_all
- [x] ~~Alembic migration~~ → ใช้ `Base.metadata.create_all()` แทน ➖

## Phase 2 — RAG Core (พระเอก)

- [x] `app/services/rag_service.py` — ingest_document, ask_question, delete_collection + metrics
- [ ] `app/routers/documents.py` — upload/list/delete + auto embed ✅ (เขียนแล้ว ยังไม่ทดสอบ)
- [ ] `app/routers/chat.py` — POST /chat + บันทึก metrics

## Phase 3 — Auth

- [x] `app/core/security.py` — ทำแล้วใน Phase 1
- [x] `app/schemas/auth.py` — RegisterRequest, LoginRequest, TokenResponse, UserResponse
- [x] `app/routers/auth.py` — register, login, /me

## Phase 4 — Case Study

- [ ] `app/schemas/chat.py` — ChatRequest, ChatResponse, ChatHistoryItem
- [ ] `app/schemas/plan.py` — PlanRequest, PlanResponse
- [ ] `app/schemas/document.py` — DocumentResponse ✅ (เขียนแล้ว)
- [ ] `app/services/plan_service.py` — generate แผนจาก RAG
- [ ] `app/routers/plans.py` — POST/GET /plans

## Phase 5 — Admin Features

- [ ] `app/routers/prompts.py` — GET /prompts, POST/DELETE (admin only)
- [ ] `app/routers/admin.py` — GET /admin/faq

---

## การเปลี่ยนแปลงจาก Design เดิม

- user model ตัด `email`, `full_name` ออก เหลือแค่ `username`
- plan model เพิ่ม `plot_name`, `response_time_ms`, `ram_used_mb`, `model_used`
- plan_service จะใช้ RAG-based แทน plain LLM
- dev ด้วย `llama3.2:3b` + `mxbai-embed-large` ก่อน ค่อย switch เป็น `gemma3:4b` + `bge-m3` ตอนเก็บ experiment

*อัปเดต: 2026-03-08*
