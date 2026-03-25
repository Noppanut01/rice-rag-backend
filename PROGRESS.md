# Progress — Rice Farming RAG Backend

> ✅ = เสร็จแล้ว | ❌ = ยังไม่ทำ | ➖ = ตัดออก | 🔧 = TODO skeleton พร้อม

---

## Phase 1 — Foundation ✅

- [x] `app/core/config.py` — BaseSettings จาก .env
- [x] `app/database.py` — PostgreSQL + SessionLocal
- [x] `app/core/security.py` — bcrypt + JWT (payload มี sub + role)
- [x] `app/dependencies.py` — get_db, get_current_user, require_admin, get_optional_user
- [x] `app/models/user.py` — UUID, username, hashed_password, role
- [x] `app/models/document.py` — UUID, filename, file_path, chroma_collection, uploaded_by
- [x] `app/models/chat.py` — UUID, question, answer, sources, metrics (user_id nullable)
- [x] `app/models/plan.py` — PlantingPlan + PlanTask (separate table)
- [x] `app/models/prompt.py` — UUID, title, content, created_by
- [x] `app/main.py` — FastAPI app, CORS, routers, create_all, auto-create uploads/ dir
- [x] ~~Alembic migration~~ → ใช้ `Base.metadata.create_all()` แทน ➖

## Phase 2 — RAG Core ✅

- [x] `app/services/rag_service.py` — ingest_document, ask_question, ask_question_no_rag, delete_document, generate_plan_from_rag ✅ + metrics
- [x] `app/routers/documents.py` — list (public), upload/delete (admin), view file (public)
- [x] `app/routers/chat.py` — POST /chat/ (optional auth), POST /chat/no-rag, GET /chat/history

## Phase 3 — Auth ✅

- [x] `app/schemas/auth.py` — RegisterRequest, LoginRequest, TokenResponse, UserResponse
- [x] `app/routers/auth.py` — register (return UserResponse), login (return token, รับ JSON)
- [x] ~~GET /auth/me~~ → ตัดออก frontend decode JWT เอง ➖

## Phase 4 — Case Study ✅

- [x] `app/schemas/chat.py` — ChatRequest, ChatResponse (sources: list[str]), ChatHistoryItem
- [x] `app/schemas/plan.py` — PlanTaskInput, PlanTaskResponse, PlanRequest (มี tasks), PlanResponse (มี tasks)
- [x] `app/schemas/document.py` — DocumentResponse (มี file_type)
- [x] `app/routers/plans.py` — POST/GET /plans/, PATCH toggle task, DELETE plan
- [x] `app/services/plan_service.py` — generate_plan ✅ (เรียก RAG → parse JSON → calc dates → return tasks)

## Phase 5 — Admin Features ✅

- [x] `app/routers/prompts.py` — GET /prompts (public), POST/DELETE (admin only), **POST /prompts/generate (admin) — LLM generate จากทุก collection, temperature=0.7, return list[{title, content}]**
- [x] `app/routers/admin.py` — GET /admin/faq (top 10 คำถามที่ถามบ่อย)
- [x] `app/services/rag_service.py` — เพิ่ม `generate_prompt_suggestions()` ดึง chunks จากทุก collection → LLM สร้าง 5 คำถาม

## Docs ✅

- [x] `API_SPEC.md` — spec ครบทุก endpoint พร้อม request/response/error/access table

---

## ถัดไป ⏭

- [ ] commit + push feature/multi-collection (backend + frontend)
- [ ] commit + push feature/generate-prompt-template (backend + frontend)
- [ ] หา/อัพโหลด PDF เอกสารเกี่ยวกับการปลูกข้าวเข้า knowledge base (rice varieties, ขั้นตอน, ปุ๋ย)
- [ ] เก็บ experiment metrics เปรียบเทียบ RAG vs no-RAG, config ต่างๆ (baseline vs optimized)

---

## การเปลี่ยนแปลงจาก Design เดิม

- user model ตัด `email`, `full_name` ออก เหลือแค่ `username`
- plan model: ตัด `plan_content` (JSONB) และ metrics ออก, เพิ่ม `variety_id`, `plot_name`, และแยก tasks เป็น table `plan_tasks`
- plan_service ใช้ RAG-based (ยังไม่ implement รอ PDF)
- ตัด Alembic ออก ใช้ `create_all()` แทน
- ตัด `/auth/me` และ `GET /plans/{id}` ออก ไม่จำเป็น
- error messages ทั้งหมดเป็นภาษาไทย
- JWT payload มี `role` ด้วย ไม่ใช่แค่ `sub` — frontend decode เอง
- `ChatResponse.sources` เป็น `list[str]` (ไม่ใช่ nested object)
- dev ด้วย `llama3.2:3b` + `mxbai-embed-large` ก่อน ค่อย switch เป็น `gemma3:4b` + `bge-m3` ตอนเก็บ experiment
- เพิ่ม `POST /chat/no-rag` สำหรับ experiment เปรียบเทียบ RAG vs plain LLM
- `/chat/` เปลี่ยนเป็น optional auth (ไม่ login ตอบได้แต่ไม่บันทึก history)
- `GET /documents/` เปลี่ยนเป็น public
- เพิ่ม `GET /documents/{id}/file` สำหรับเปิดอ่านไฟล์ใน browser
- `get_optional_user` dependency ใน dependencies.py

*อัปเดต: 2026-03-25*
