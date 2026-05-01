# Rice Expert Code Reading Checklist

ใช้ checklist นี้เพื่ออ่านโค้ดตาม dependency จริงของระบบ ไม่ใช่อ่านเรียงชื่อไฟล์แบบสุ่ม

หลักการอ่าน:
- อ่าน Backend ก่อน เพื่อเข้าใจข้อมูล กฎธุรกิจ และ API contract
- อ่าน Frontend ต่อ เพื่อดูว่า UI เรียก API และแปลงข้อมูลอย่างไร
- อ่าน UI primitive ท้ายสุด เพราะเป็น component พื้นฐาน ไม่ใช่ business logic

## 0. Project Entry Points

- [ ] `/Users/noppanut/Developer/rice-rag-backend/requirements.txt` — dependency backend ที่ใช้จริง
- [ ] `/Users/noppanut/Developer/Webriceexpert/package.json` — dependency และ script frontend
- [ ] `/Users/noppanut/Developer/rice-rag-backend/DEMO_SCRIPT.md` — flow demo และคำอธิบาย baseline plan
- [ ] `/Users/noppanut/Developer/rice-rag-backend/SYSTEM_TEST_CASES.csv` — test cases ทั้งระบบ

## 1. Backend Foundation

อ่านกลุ่มนี้ก่อน เพราะทุก router/service พึ่งพา config/database/auth

- [ ] `app/__init__.py` — package marker
- [ ] `app/core/__init__.py` — core package marker
- [ ] `app/core/config.py` — env/config เช่น `DATABASE_URL`, Gemini, Chroma, JWT, retrieval settings
- [ ] `app/database.py` — SQLAlchemy engine, session, Base
- [ ] `app/core/security.py` — hash password, verify password, create/decode JWT
- [ ] `app/dependencies.py` — `get_db`, `get_current_user`, `get_optional_user`, `require_admin`

เข้าใจให้ได้ก่อนอ่านต่อ:
- request ที่ต้อง login ใช้ `get_current_user`
- request ที่ guest ใช้ได้แต่ login แล้วบันทึก history ได้ ใช้ `get_optional_user`
- admin endpoint ใช้ `require_admin`

## 2. Backend Data Models

อ่าน model ก่อน schema/router เพื่อเข้าใจตารางจริงใน PostgreSQL

- [ ] `app/models/__init__.py` — import models
- [ ] `app/models/user.py` — users, role user/admin
- [ ] `app/models/variety.py` — rice varieties, growth stage, fertilizer rates, active flag
- [ ] `app/models/plan.py` — planting_plans และ plan_tasks/checklist
- [ ] `app/models/document.py` — metadata เอกสารและ collection
- [ ] `app/models/chat.py` — chat history + RAG metrics
- [ ] `app/models/prompt.py` — prompt templates

จุดสำคัญ:
- `plan_tasks.is_completed` คือ checklist ที่ track งานจริง
- `planting_plans.resources_snapshot` คือผลคำนวณ resource ณ ตอนสร้าง/แก้แผน
- `rice_varieties.fert1_formula` ยังเป็น legacy DB column แต่ไม่ expose UI/API แล้ว

## 3. Backend API Schemas

อ่าน schema หลัง models เพื่อรู้ request/response contract

- [ ] `app/schemas/__init__.py` — schema package marker
- [ ] `app/schemas/auth.py` — login/register/user role payloads
- [ ] `app/schemas/plan.py` — create/update/clone plan และ PlanResponse
- [ ] `app/schemas/document.py` — document response
- [ ] `app/schemas/chat.py` — chat request/response/history
- [ ] `app/schemas/prompt.py` — prompt template request/response

จุดสำคัญ:
- `PlanResponse.tasks[].is_completed` ส่งสถานะ checklist กลับ frontend
- `PlanResources` มีสูตรปุ๋ยสองช่วงที่ dashboard แสดง

## 4. Backend Services

อ่าน service ก่อน router เพราะ router ส่วนใหญ่แค่รับ request แล้วเรียก service

- [ ] `app/services/__init__.py` — service package marker
- [ ] `app/services/plan_service.py` — rule-based plan generation
- [ ] `app/services/rag_service.py` — document ingestion, ChromaDB, RAG search, Gemini answer

อ่าน `plan_service.py` ตามลำดับ:
- [ ] constants: `SOIL_FERT1_FORMULA`, `SOIL_FERT_MULTIPLIER`, `PLANTING_DAY`
- [ ] `_build_tasks()` — สร้าง task ตามวิธีปลูกและระยะการเจริญเติบโต
- [ ] `calculate_resources()` — คำนวณเมล็ดพันธุ์ ปุ๋ย ถาดเพาะกล้า
- [ ] `PlanService.generate_plan()` — validation ข้าวไวแสง, คำนวณวัน, สร้าง tasks/resources

อ่าน `rag_service.py` ตามลำดับ:
- [ ] init Gemini embedding/LLM/splitter
- [ ] `load_collections()` — โหลด Chroma collection
- [ ] `_search()` — retrieval ด้วย MMR/similarity ตาม config
- [ ] `ingest_document()` — PDF/DOCX/TXT → chunks → embeddings
- [ ] `ask_question()` — RAG answer + metrics
- [ ] `ask_question_no_rag()` — hidden comparison mode
- [ ] `delete_document()` — ลบ vector + file

จุดสำคัญ:
- ปุ๋ยช่วงแตกกอใช้สูตรตามดินเสมอ
- ปุ๋ยช่วงกำเนิดช่อดอกใช้ `fert2_formula` จากพันธุ์
- ข้าวไวแสง backend รับ start date เฉพาะ มิ.ย.-ก.ค.
- `RETRIEVAL_K` ปัจจุบันมาจาก config ค่า default 5

## 5. Backend Routers

อ่าน router ตามลำดับจาก auth → public content → domain logic → admin

- [ ] `app/routers/__init__.py` — router package marker
- [ ] `app/routers/auth.py` — register/login/JWT
- [ ] `app/routers/varieties.py` — public list + admin CRUD พันธุ์ข้าว
- [ ] `app/routers/plans.py` — create/list/update/clone/delete plan และ toggle task
- [ ] `app/routers/documents.py` — list/open/upload/delete documents
- [ ] `app/routers/chat.py` — RAG chat, no-rag, history
- [ ] `app/routers/prompts.py` — prompt templates + AI generate suggestions
- [ ] `app/routers/admin.py` — users, FAQ, gaps

จุดสำคัญใน `plans.py`:
- [ ] `create_plan()` — ใช้ variety id, check supported method, สร้าง tasks/resources
- [ ] `get_plans()` — ดึงทุก plan ของ current user
- [ ] `toggle_task()` — toggle `is_completed`
- [ ] `update_plan()` — แก้ชื่อ/พื้นที่/ดิน แล้ว recalc resources ไม่แตะ tasks
- [ ] `clone_plan()` — สร้างแผนใหม่จาก plan เดิม + start date ใหม่
- [ ] `delete_plan()` — ลบ plan และ tasks

จุดสำคัญใน `varieties.py`:
- [ ] `_validate_growth_stages()` — วันต้องเรียง แตกกอ < กำเนิดช่อดอก < ออกรวง < เก็บเกี่ยว
- [ ] `_validate_fertilizer()` — rate ปุ๋ยสองช่วงและสูตรปุ๋ยกำเนิดช่อดอกต้องครบ
- [ ] create/update ไม่รับ `fert1_formula` จาก API แล้ว แต่ set legacy DB column เป็น `""`

## 6. Backend App Startup

อ่านท้าย backend หลังเข้าใจ routers/services แล้ว

- [ ] `app/main.py` — FastAPI app, CORS, create_all, include routers, startup load Chroma collections

จุดสำคัญ:
- `Base.metadata.create_all()` ใช้สร้างตารางอัตโนมัติ ไม่มี Alembic migration
- startup โหลด collection จาก `rice_varieties` ทั้งหมด + `general`

## 7. Frontend Foundation

อ่าน frontend base ก่อน pages เพื่อเข้าใจ API/auth/router

- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/App.tsx` — entry ของ React router
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/routes.tsx` — route tree, protected routes, admin route guard
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/lib/api.ts` — `apiFetch`, token header, API base URL
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/lib/auth.ts` — login/register/localStorage role
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/components/ProtectedRoute.tsx` — auth guard + admin guard
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/components/AppLayout.tsx` — layout, sidebar, mobile menu, FloatingChat, PlansProvider

จุดสำคัญ:
- `/app/*` ต้อง login
- `/app/admin` ต้อง role admin
- menu admin ซ่อนจาก user และ route guard redirect user กลับ `/app/plots`

## 8. Frontend Shared Types and Utilities

- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/lib/planTypes.ts` — frontend plan/task/resource types
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/lib/plantingMethod.ts` — planting method keys/labels/descriptions
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/lib/dateUtils.ts` — Buddhist Era date formatting
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/lib/taskIcons.tsx` — icon mapping by task name
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/lib/planGenerator.ts` — date helper legacy/utility

## 9. Frontend Plan State

อ่านก่อน pages ที่ใช้ plan ทั้งหมด

- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/contexts/PlansContext.tsx` — โหลด plans, map backend→frontend, create/update/clone/delete/toggle task

อ่านตามลำดับในไฟล์:
- [ ] backend response interfaces
- [ ] `mapTask()` / `mapPlan()`
- [ ] `refreshVarieties()`
- [ ] `fetchPlans()`
- [ ] `createPlan()`
- [ ] `toggleTask()`
- [ ] `updatePlan()`
- [ ] `clonePlan()`
- [ ] `deletePlan()`
- [ ] progress helpers: `getDaysSinceStart`, `getTotalDays`, `getProgressPercent`, `getCurrentStageName`, `getUpcomingTasks`

จุดสำคัญ:
- `getProgressPercent()` คือ progress ตามเวลา ไม่ใช่ checklist completion
- checklist completion มาจาก `tasks.filter(t => t.isCompleted)`

## 10. Frontend Guest/Auth Pages

- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/pages/Landing.tsx` — guest landing, public chat, public docs, varieties
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/pages/Login.tsx` — login form
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/pages/Register.tsx` — register form

จุดสำคัญ:
- Landing chat ใช้ `/chat/` แบบ guest ได้ แต่ไม่ save history
- Login decode JWT เพื่อเก็บ role ใน localStorage

## 11. Frontend User Plan Flow

อ่านตาม user journey จริง

- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/pages/Plots.tsx` — list plans, progress cards, delete plan
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/pages/CreatePlan.tsx` — 3-step wizard สร้างแผน
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/pages/PlotDashboard.tsx` — dashboard, resources, checklist, edit, clone, print
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/pages/Calendar.tsx` — calendar tasks by date and growth stages
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/pages/Knowledge.tsx` — documents grouped by collection

จุดสำคัญใน `CreatePlan.tsx`:
- [ ] โหลด varieties จาก `/varieties/`
- [ ] map `collection_name` เป็น frontend `varietyId`
- [ ] filter supported planting methods
- [ ] disable date สำหรับข้าวไวแสงนอก มิ.ย.-ก.ค.
- [ ] submit ผ่าน `createPlan()` ใน PlansContext

จุดสำคัญใน `PlotDashboard.tsx`:
- [ ] progress circle = ความคืบหน้าตามเวลา
- [ ] checklist = งานจริงทำเสร็จหรือยัง
- [ ] overdue task = task ที่เลยวันและยังไม่ completed
- [ ] edit recalculates resources only
- [ ] clone creates a new plan with new start date

## 12. Frontend Chat

- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/components/FloatingChat.tsx` — authenticated chat widget, plan context, sources, history, no-rag mode

อ่านตามลำดับ:
- [ ] message interfaces
- [ ] `toDisplayUserQuestion()`
- [ ] load prompt templates
- [ ] load chat history
- [ ] build `planContext`
- [ ] send `/chat/` or `/chat/no-rag`
- [ ] render sources

จุดสำคัญ:
- `plan_context` ถูกสร้างจาก current plan ใน `usePlans()`
- history ถูกส่ง 6 message ล่าสุด
- collection ใช้ `plan.varietyId` ซึ่งถูก map เป็น `collection_name`

## 13. Frontend Admin

อ่าน admin shell ก่อน panel ย่อย

- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/pages/Admin.tsx` — admin tabs: users/docs/prompts/varieties/gaps
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/pages/VarietiesAdminPanel.tsx` — CRUD/validation พันธุ์ข้าว

จุดสำคัญใน `Admin.tsx`:
- [ ] users tab → `/admin/users`, update role
- [ ] docs tab → `/documents/`, `/documents/upload`, delete docs
- [ ] prompts tab → `/prompts/`, `/prompts/generate`, FAQ
- [ ] varieties tab → `VarietiesAdminPanel`
- [ ] gaps tab → `/admin/gaps`

จุดสำคัญใน `VarietiesAdminPanel.tsx`:
- [ ] field order + scroll to first error
- [ ] validate name/collection/methods/growth stages/fertilizer
- [ ] no `fert1_formula` input
- [ ] fertilizer tillering formula shown as automatic by soil
- [ ] fertilizer panicle formula saved as `fert2_formula`
- [ ] delete variety also removes linked documents

## 14. Frontend Shared Components

อ่านหลัง business pages เพราะเป็น UI plumbing

- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/components/DeleteConfirmDialog.tsx`
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/components/EmptyState.tsx`
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/components/LoadingScreen.tsx`

## 15. Frontend UI Primitives

อ่านท้ายสุดหรือข้ามได้ถ้าเป้าหมายคือเข้าใจ business logic

- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/components/ui/alert-dialog.tsx`
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/components/ui/badge.tsx`
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/components/ui/button.tsx`
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/components/ui/calendar.tsx`
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/components/ui/card.tsx`
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/components/ui/checkbox.tsx`
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/components/ui/dialog.tsx`
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/components/ui/input.tsx`
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/components/ui/label.tsx`
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/components/ui/popover.tsx`
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/components/ui/progress.tsx`
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/components/ui/select.tsx`
- [ ] `/Users/noppanut/Developer/Webriceexpert/src/app/components/ui/utils.ts`

## 16. Recommended Reading Sessions

ถ้าอ่านวันเดียว:

- [ ] Session 1: Backend foundation + models + schemas
- [ ] Session 2: `plan_service.py` + `plans.py` + `varieties.py`
- [ ] Session 3: `rag_service.py` + `chat.py` + `documents.py`
- [ ] Session 4: Frontend `api.ts`, `auth.ts`, `routes.tsx`, `PlansContext.tsx`
- [ ] Session 5: `CreatePlan.tsx`, `Plots.tsx`, `PlotDashboard.tsx`, `Calendar.tsx`
- [ ] Session 6: `FloatingChat.tsx`, `Admin.tsx`, `VarietiesAdminPanel.tsx`

ถ้ามีเวลาน้อยก่อนสอบ:

- [ ] อ่าน `plan_service.py`
- [ ] อ่าน `plans.py`
- [ ] อ่าน `varieties.py`
- [ ] อ่าน `rag_service.py`
- [ ] อ่าน `chat.py`
- [ ] อ่าน `PlansContext.tsx`
- [ ] อ่าน `CreatePlan.tsx`
- [ ] อ่าน `PlotDashboard.tsx`
- [ ] อ่าน `FloatingChat.tsx`
- [ ] อ่าน `Admin.tsx`
- [ ] อ่าน `VarietiesAdminPanel.tsx`

## 17. Current System Differences From The Old HTML Overview

- [ ] Update old docs: retrieval default is `RETRIEVAL_K=5`, not hardcoded `k=3`
- [ ] Update old docs: frontend/backend photoperiod currently both use มิ.ย.-ก.ค.
- [ ] Update old docs: `fert1_formula` is no longer exposed in UI/API; it remains only as legacy DB column/internal service parameter
- [ ] Update old docs: fertilizer labels are now growth-stage based: ปุ๋ยช่วงแตกกอ / ปุ๋ยช่วงกำเนิดช่อดอก
- [ ] Update old docs: frontend admin route guard now exists
- [ ] Update old docs: large unused UI component set and unused dependencies were removed
- [ ] Update old docs: backend `alembic` and `psutil` were removed from requirements
- [ ] Update old docs: `DEMO_SCRIPT.md` and `SYSTEM_TEST_CASES.csv` now exist as project support artifacts

## 18. Final Mental Model

- [ ] Backend owns truth: DB models, validation, plan generation, RAG, permissions
- [ ] Frontend owns interaction: wizard, dashboard, checklist, calendar, admin CMS
- [ ] Plan generation is rule-based, not AI-generated
- [ ] RAG is for Q&A and explanation, not for creating the plan
- [ ] Progress percent tracks crop-cycle time
- [ ] Checklist tracks actual task completion
- [ ] The plan is a baseline schedule; real work can lag and become overdue
