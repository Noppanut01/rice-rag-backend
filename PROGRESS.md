# Progress — Rice Farming RAG Backend

> ✅ = เสร็จแล้ว | ❌ = ยังไม่ทำ | ➖ = ตัดออก

---

## Phase 1 — Foundation ✅

- [x] `app/core/config.py` — BaseSettings จาก .env
- [x] `app/database.py` — PostgreSQL + SessionLocal
- [x] `app/core/security.py` — bcrypt + JWT (payload มี sub + role)
- [x] `app/dependencies.py` — get_db, get_current_user, require_admin
- [x] `app/models/user.py` — UUID, username, hashed_password, role
- [x] `app/models/document.py` — UUID, filename, file_path, chroma_collection, uploaded_by
- [x] `app/models/chat.py` — UUID, question, answer, sources, metrics (user_id NOT NULL)
- [x] `app/models/plan.py` — UUID, variety_name, start_date, area_rai, plot_name, metrics
- [x] `app/models/prompt.py` — UUID, title, content, created_by
- [x] `app/main.py` — FastAPI app, CORS, routers, create_all
- [x] ~~Alembic migration~~ → ใช้ `Base.metadata.create_all()` แทน ➖

## Phase 2 — RAG Core ✅

- [x] `app/services/rag_service.py` — ingest_document, ask_question, delete_document + metrics
- [x] `app/routers/documents.py` — upload/list/delete + auto embed (admin only)
- [x] `app/routers/chat.py` — POST /chat/, GET /chat/history + บันทึก metrics

## Phase 3 — Auth ✅

- [x] `app/schemas/auth.py` — RegisterRequest, LoginRequest, TokenResponse, UserResponse
- [x] `app/routers/auth.py` — register (return UserResponse), login (return token, รับ JSON)
- [x] ~~GET /auth/me~~ → ตัดออก ไม่จำเป็น ➖

## Phase 4 — Case Study ✅

- [x] `app/schemas/chat.py` — ChatRequest, ChatResponse (sources: list[str]), ChatHistoryItem
- [x] `app/schemas/plan.py` — PlanRequest, PlanResponse (มี plot_name)
- [x] `app/schemas/document.py` — DocumentResponse (มี file_type)
- [x] `app/services/plan_service.py` — generate แผนจาก RAG
- [x] `app/routers/plans.py` — POST/GET /plans

## Phase 5 — Admin Features ✅

- [x] `app/routers/prompts.py` — GET /prompts (public), POST/DELETE (admin only)
- [x] `app/routers/admin.py` — GET /admin/faq (top 10 คำถามที่ถามบ่อย)

## Docs ✅

- [x] `API_SPEC.md` — spec ครบทุก endpoint พร้อม request/response/error

---

## ถัดไป ⏭

- [ ] ทดสอบ upload เอกสารจริง แล้วลอง RAG ตอบจาก context
- [ ] เก็บ experiment metrics เปรียบเทียบ config ต่างๆ (baseline vs optimized)

---

## การเปลี่ยนแปลงจาก Design เดิม

- user model ตัด `email`, `full_name` ออก เหลือแค่ `username`
- plan model เพิ่ม `plot_name`, `response_time_ms`, `ram_used_mb`, `model_used`
- plan_service ใช้ RAG-based แทน plain LLM
- ตัด Alembic ออก ใช้ `create_all()` แทน
- ตัด `/auth/me` และ `GET /plans/{id}` ออก ไม่จำเป็น
- error messages ทั้งหมดเป็นภาษาไทย
- JWT payload มี `role` ด้วย ไม่ใช่แค่ `sub`
- `ChatResponse.sources` เป็น `list[str]` (ไม่ใช่ nested object)
- dev ด้วย `llama3.2:3b` + `mxbai-embed-large` ก่อน ค่อย switch เป็น `gemma3:4b` + `bge-m3` ตอนเก็บ experiment

*อัปเดต: 2026-03-09*
