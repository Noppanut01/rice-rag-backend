# Rice Expert Code Reading Checklist แบบมีคำอธิบาย

ใช้ส่วนนี้อ่านโค้ดตามลำดับที่ระบบพึ่งพากันจริง เพื่อไม่หลงว่าไฟล์ไหนควรอ่านก่อนหลัง

หลักคิด:
- อ่าน Backend ก่อน เพราะเป็นแหล่งความจริงของข้อมูล กฎธุรกิจ สิทธิ์ และ API
- อ่าน Frontend หลังจากเข้าใจ API แล้ว จะเห็นว่า UI ส่งข้อมูลไป backend อย่างไร
- อ่าน UI components ท้ายสุด เพราะเป็นส่วนแสดงผล ไม่ใช่ logic หลัก

## 0. ภาพรวมโปรเจคและไฟล์ประกอบ

- [ ] `requirements.txt` — ดู dependency backend ทั้งหมด เช่น FastAPI, SQLAlchemy, LangChain, Chroma, Gemini
- [ ] `/Users/noppanut/Developer/Webriceexpert/package.json` — ดู dependency frontend และ script ที่รันได้ เช่น `npm run build`
- [ ] `DEMO_SCRIPT.md` — ใช้ซ้อม flow demo หน้ากรรมการตั้งแต่ guest, user, admin
- [ ] `SYSTEM_TEST_CASES.csv` — ใช้เป็น checklist manual test ทั้งระบบ แยก role/feature/edge/security

## 1. Backend Foundation: พื้นฐานที่ทุกไฟล์พึ่งพา

- [ ] `app/__init__.py` — ไฟล์ marker ให้ Python รู้ว่า `app` เป็น package
- [ ] `app/core/__init__.py` — marker ของ core package ไม่มี logic แต่ควรรู้ตำแหน่ง
- [ ] `app/core/config.py` — อ่าน config จาก `.env` เช่น database, Gemini key/model, Chroma path, JWT, retrieval settings
- [ ] `app/database.py` — สร้าง SQLAlchemy engine/session/Base เป็นจุดเริ่มของ DB ทั้งระบบ
- [ ] `app/core/security.py` — จัดการ password hash, verify password, สร้างและ decode JWT token
- [ ] `app/dependencies.py` — รวม dependency สำคัญของ FastAPI เช่น เปิด DB session, หา current user, optional user, admin guard

ต้องเข้าใจก่อนอ่านต่อ:
- [ ] `get_current_user` — endpoint ที่ต้อง login ใช้อันนี้ ถ้า token ผิดจะ 401
- [ ] `get_optional_user` — chat ใช้ได้ทั้ง guest/user ถ้า login จะบันทึก history
- [ ] `require_admin` — endpoint admin ใช้อันนี้เพื่อกัน user ธรรมดา

## 2. Backend Models: ตารางจริงในฐานข้อมูล

- [ ] `app/models/__init__.py` — import models เพื่อให้ `Base.metadata.create_all()` เห็นทุกตาราง
- [ ] `app/models/user.py` — ตารางผู้ใช้ เก็บ username, hashed password, role user/admin
- [ ] `app/models/variety.py` — ตารางพันธุ์ข้าว เก็บระยะเจริญเติบโต วิธีปลูกที่รองรับ ปุ๋ย และ collection ของ RAG
- [ ] `app/models/plan.py` — ตารางแผนปลูกและรายการงาน เป็นหัวใจของระบบ tracking
- [ ] `app/models/document.py` — metadata เอกสารที่ admin upload และผูกกับ Chroma collection
- [ ] `app/models/chat.py` — ประวัติ chat และ metric ของ RAG เช่น chunks, token, response time
- [ ] `app/models/prompt.py` — prompt template ที่ admin สร้างให้ user กดถามได้

จุดที่ควรจำ:
- [ ] `PlanTask.is_completed` — checkbox/todo-list บันทึกจริงใน DB
- [ ] `PlantingPlan.resources_snapshot` — เก็บผลคำนวณเมล็ด/ปุ๋ย ณ ตอนสร้างหรือแก้แผน
- [ ] `RiceVariety.fert1_formula` — เป็น legacy column เหลือใน DB แต่ UI/API ไม่ให้กรอกแล้ว

## 3. Backend Schemas: รูปแบบ request/response

- [ ] `app/schemas/__init__.py` — marker ของ schema package
- [ ] `app/schemas/auth.py` — payload login/register และ response user/role
- [ ] `app/schemas/plan.py` — contract ของ create/update/clone plan, resource, task, response ทั้งแผน
- [ ] `app/schemas/document.py` — response เอกสารที่ frontend เอาไปแสดงใน Knowledge/Admin
- [ ] `app/schemas/chat.py` — request/response chat, sources, metric, history item
- [ ] `app/schemas/prompt.py` — request/response ของ prompt templates

จุดที่ควรจำ:
- [ ] `PlanResponse.tasks[].is_completed` — ส่งสถานะติ๊กงานกลับ frontend
- [ ] `PlanResources` — เป็นตัวกำหนดว่า dashboard แสดงเมล็ดพันธุ์และปุ๋ยอะไร

## 4. Backend Services: logic หลักที่ไม่ใช่ HTTP

- [ ] `app/services/__init__.py` — marker ของ service package
- [ ] `app/services/plan_service.py` — logic สร้างแผนแบบ rule-based ไม่ใช้ AI สร้างแผน
- [ ] `app/services/rag_service.py` — logic ingest เอกสาร, ค้น Chroma, สร้าง prompt, เรียก Gemini

อ่าน `plan_service.py` ตามลำดับ:
- [ ] constants — ดูสูตรปุ๋ยตามดิน, multiplier ตามดิน, วันลงแปลงของแต่ละวิธีปลูก
- [ ] `_build_tasks()` — ดูว่าแต่ละวิธีปลูกสร้าง task อะไรบ้าง และ task แต่ละตัวอยู่ day ไหน
- [ ] `calculate_resources()` — ดูการคำนวณ seed, fertilizer, tray ตามพื้นที่/ดิน/วิธีปลูก
- [ ] `PlanService.generate_plan()` — ดู flow รวม: validate ข้าวไวแสง, คำนวณวัน, สร้าง tasks/resources

อ่าน `rag_service.py` ตามลำดับ:
- [ ] `__init__` — ดู model Gemini, embedding, splitter, vectorstores ที่ระบบใช้
- [ ] `load_collections()` — ดูการโหลด Chroma collection ตอน startup หรือเพิ่มพันธุ์
- [ ] `_search()` — ดู retrieval ว่าค้น collection ไหน ใช้ MMR/similarity และคืน chunks อย่างไร
- [ ] `ingest_document()` — ดู pipeline PDF/DOCX/TXT → chunk → embedding → Chroma
- [ ] `ask_question()` — ดู RAG prompt, context, sources, metrics, response
- [ ] `ask_question_no_rag()` — ดูโหมดเทียบแบบไม่ใช้เอกสาร
- [ ] `delete_document()` — ดูการลบ vector และไฟล์เมื่อ admin ลบเอกสาร

## 5. Backend Routers: API ที่ frontend เรียก

- [ ] `app/routers/__init__.py` — marker ของ router package
- [ ] `app/routers/auth.py` — API สมัคร/ล็อกอิน และการสร้าง JWT
- [ ] `app/routers/varieties.py` — API พันธุ์ข้าว public list และ admin create/update/delete
- [ ] `app/routers/plans.py` — API สร้างแผน ดึงแผน แก้แผน clone ลบแผน และ toggle task
- [ ] `app/routers/documents.py` — API list/open/upload/delete เอกสารและ collection
- [ ] `app/routers/chat.py` — API chat RAG, no-rag, history
- [ ] `app/routers/prompts.py` — API prompt templates และ generate suggestions
- [ ] `app/routers/admin.py` — API admin users, FAQ, knowledge gaps

อ่านลึกใน `plans.py`:
- [ ] `_resolve_fert()` — ดึงอัตราปุ๋ยและสูตรปุ๋ยช่วงกำเนิดช่อดอกจากพันธุ์
- [ ] `create_plan()` — รับข้อมูลจาก wizard แล้วสร้าง plan/tasks/resources
- [ ] `get_plans()` — ดึงแผนของ user ปัจจุบันทั้งหมด
- [ ] `toggle_task()` — เปลี่ยน `is_completed` ของ task ใช้กับ checklist
- [ ] `update_plan()` — แก้ชื่อ/พื้นที่/ดิน แล้วคำนวณ resources ใหม่โดยไม่ล้าง task
- [ ] `clone_plan()` — สร้างแผนใหม่จากแผนเดิมเมื่ออยากเริ่มรอบใหม่
- [ ] `delete_plan()` — ลบแผนและ task ของแผนนั้น

อ่านลึกใน `varieties.py`:
- [ ] `_validate_growth_stages()` — กันวันแตกกอ/กำเนิดช่อดอก/ออกรวง/เก็บเกี่ยวเรียงผิด
- [ ] `_validate_fertilizer()` — กันข้อมูลปุ๋ยว่างหรือค่าติดลบ
- [ ] `create_variety()` — เพิ่มพันธุ์ใหม่และสร้าง Chroma collection ให้พร้อมอัปโหลดเอกสาร
- [ ] `update_variety()` — แก้ข้อมูลพันธุ์ มีผลกับแผนใหม่ ไม่ย้อนแก้แผนเก่า
- [ ] `delete_variety()` — ลบพันธุ์พร้อมเอกสารและ vector ที่ผูกกับ collection

## 6. Backend Startup

- [ ] `app/main.py` — จุดประกอบ FastAPI ทั้งระบบ: CORS, create tables, include routers, startup load RAG collections

จุดที่ควรจำ:
- [ ] `Base.metadata.create_all()` — โปรเจคนี้สร้างตารางอัตโนมัติ ยังไม่มี migration
- [ ] startup โหลด `rice_varieties` ทั้งหมด + `general` เข้า Chroma vectorstores

## 7. Frontend Foundation: โครงก่อนเข้าแต่ละหน้า

- [ ] `src/app/App.tsx` — entry component ที่ render `RouterProvider`
- [ ] `src/app/routes.tsx` — route tree ทั้งระบบ และ guard `/app/admin`
- [ ] `src/app/lib/api.ts` — helper เรียก backend, ใส่ token, handle error
- [ ] `src/app/lib/auth.ts` — login/register, เก็บ token/username/role ใน localStorage
- [ ] `src/app/components/ProtectedRoute.tsx` — กัน route ที่ต้อง login และ route ที่ต้องเป็น admin
- [ ] `src/app/components/AppLayout.tsx` — layout หลัง login, sidebar, mobile menu, logout, FloatingChat, PlansProvider

จุดที่ควรจำ:
- [ ] `/app/*` ต้อง login
- [ ] `/app/admin` ต้อง role admin
- [ ] backend ยังกันสิทธิ์ซ้ำด้วย `require_admin`

## 8. Frontend Shared Types and Utils

- [ ] `src/app/lib/planTypes.ts` — type หลักของ plan/task/resource ฝั่ง frontend
- [ ] `src/app/lib/plantingMethod.ts` — key/label/description ของ transplant, broadcast, throw
- [ ] `src/app/lib/dateUtils.ts` — format วันที่ พ.ศ. สำหรับ UI ไทย
- [ ] `src/app/lib/taskIcons.tsx` — map ชื่องานเป็น icon ใน dashboard
- [ ] `src/app/lib/planGenerator.ts` — helper วันที่บางส่วน เป็น legacy/utility ไม่ใช่ตัวสร้างแผนหลักแล้ว

## 9. Frontend Plan State

- [ ] `src/app/contexts/PlansContext.tsx` — state กลางของแผนทั้งหมด เป็นตัวเชื่อม API plan กับทุกหน้า user

อ่านในไฟล์นี้ตามลำดับ:
- [ ] backend interfaces — ดู response จาก backend ก่อนถูก map เป็น frontend type
- [ ] `mapTask()` / `mapPlan()` — ดูการแปลง snake_case เป็น camelCase
- [ ] `refreshVarieties()` — map ระหว่าง UUID กับ `collection_name`
- [ ] `fetchPlans()` — โหลดแผนทั้งหมดหลัง login
- [ ] `createPlan()` — ส่งข้อมูลจาก wizard ไป POST `/plans/`
- [ ] `toggleTask()` — ส่ง PATCH เพื่อบันทึก checkbox จริง
- [ ] `updatePlan()` — แก้พื้นที่/ดิน/ชื่อแปลง
- [ ] `clonePlan()` — สร้างแผนใหม่จากแผนเดิม
- [ ] `deletePlan()` — ลบแผน
- [ ] progress helpers — ดูความต่างระหว่าง progress ตามเวลา กับ checklist completion

จุดที่ควรจำ:
- [ ] `getProgressPercent()` = ความคืบหน้าตามเวลาในวงจรปลูก
- [ ] `isCompleted` = สถานะงานจริงที่ user ติ๊กใน checklist

## 10. Frontend Guest/Auth Pages

- [ ] `src/app/pages/Landing.tsx` — หน้า guest มี intro, public chat, public docs, varieties
- [ ] `src/app/pages/Login.tsx` — form login และ redirect หลัง login
- [ ] `src/app/pages/Register.tsx` — form สมัครสมาชิกและ validate confirm password

จุดที่ควรจำ:
- [ ] Landing chat ใช้ได้โดยไม่ login แต่ไม่ save history
- [ ] login decode JWT เพื่อเก็บ role แล้วแสดงเมนู admin เฉพาะ admin

## 11. Frontend User Plan Flow

- [ ] `src/app/pages/Plots.tsx` — หน้า list แปลงนา แสดง progress card และลบแผน
- [ ] `src/app/pages/CreatePlan.tsx` — wizard 3 ขั้น: เลือกพันธุ์ เลือกวัน กรอกรายละเอียดแปลง
- [ ] `src/app/pages/PlotDashboard.tsx` — dashboard หลักของแผน มี progress, resources, checklist, edit, clone, print
- [ ] `src/app/pages/Calendar.tsx` — ปฏิทินงานของแผนที่เลือกและระยะการเจริญเติบโต
- [ ] `src/app/pages/Knowledge.tsx` — คลังเอกสารสำหรับ user ดูเอกสารอ้างอิง

จุดที่ควรจำใน `CreatePlan.tsx`:
- [ ] โหลดพันธุ์จาก `/varieties/`
- [ ] ใช้ `collection_name` เป็น frontend variety id เพื่อส่งกลับไป map เป็น UUID
- [ ] แสดงวิธีปลูกเฉพาะที่พันธุ์รองรับ
- [ ] ข้าวไวแสงเลือกวันเริ่มได้เฉพาะ มิ.ย.-ก.ค.
- [ ] submit ผ่าน `PlansContext.createPlan()`

จุดที่ควรจำใน `PlotDashboard.tsx`:
- [ ] วงกลม `%` คือ progress ตามเวลา ไม่ใช่จำนวนงานที่เสร็จ
- [ ] checklist คือสถานะงานจริงที่ user ทำแล้ว/ยังไม่ทำ
- [ ] งานเลยวันและยังไม่เสร็จจะแสดงเป็น overdue
- [ ] edit แผนคำนวณ resource ใหม่ แต่ไม่ล้าง task/checklist
- [ ] clone ใช้เมื่ออยากเริ่มรอบใหม่หรือเลื่อนแผนใหญ่

## 12. Frontend Chat

- [ ] `src/app/components/FloatingChat.tsx` — chat หลัง login ที่แนบ context แผนปัจจุบันให้ AI

อ่านในไฟล์นี้ตามลำดับ:
- [ ] message types — ดู shape ของข้อความใน UI
- [ ] `toDisplayUserQuestion()` — ตัด context เก่าออกจากคำถามที่โหลดจาก history
- [ ] load prompt templates — โหลดคำถามแนะนำ
- [ ] load chat history — โหลดประวัติแชทของ user
- [ ] build `planContext` — สรุปแผนปัจจุบัน เช่น พันธุ์ ดิน ระยะ งานวันนี้ งานถัดไป
- [ ] send `/chat/` หรือ `/chat/no-rag` — ส่งคำถามไป backend
- [ ] render sources — แสดงเอกสารอ้างอิงที่ RAG ดึงมา

## 13. Frontend Admin

- [ ] `src/app/pages/Admin.tsx` — shell ของ admin มี tabs users/docs/prompts/varieties/gaps
- [ ] `src/app/pages/VarietiesAdminPanel.tsx` — form CRUD พันธุ์ข้าวและ validation ทางเกษตร

จุดที่ควรจำใน `Admin.tsx`:
- [ ] users tab — จัดการ role user/admin
- [ ] docs tab — upload/delete/open documents
- [ ] prompts tab — เพิ่ม prompt template, generate ด้วย AI, ดู FAQ
- [ ] varieties tab — ฝัง `VarietiesAdminPanel`
- [ ] gaps tab — ดูคำถามที่ AI ไม่มีเอกสารรองรับหรือใช้ความรู้ทั่วไป

จุดที่ควรจำใน `VarietiesAdminPanel.tsx`:
- [ ] มี field validation และ scroll ไปช่องแรกที่ผิด
- [ ] ไม่ให้กรอก `fert1_formula` แล้ว เพราะสูตรช่วงแตกกอขึ้นกับดิน
- [ ] ปุ๋ยช่วงแตกกอแสดงสูตรอัตโนมัติตามดิน
- [ ] ปุ๋ยช่วงกำเนิดช่อดอกใช้ `fert2_formula` จากพันธุ์
- [ ] delete พันธุ์จะลบเอกสารและ vector ที่ผูกกับ collection ด้วย

## 14. Frontend Shared Components

- [ ] `src/app/components/DeleteConfirmDialog.tsx` — dialog ยืนยันก่อนลบ ใช้กับเอกสาร prompt และพันธุ์
- [ ] `src/app/components/EmptyState.tsx` — component แสดงสถานะไม่มีข้อมูล
- [ ] `src/app/components/LoadingScreen.tsx` — component loading กลางของหน้า

## 15. Frontend UI Primitives

อ่านท้ายสุดหรือข้ามได้ถ้าเป้าหมายคือเข้าใจระบบ ไม่ใช่แก้ UI component

- [ ] `src/app/components/ui/alert-dialog.tsx` — primitive dialog ยืนยัน/แจ้งเตือน
- [ ] `src/app/components/ui/badge.tsx` — ป้ายสถานะ เช่น stage, overdue
- [ ] `src/app/components/ui/button.tsx` — ปุ่มมาตรฐานของระบบ
- [ ] `src/app/components/ui/calendar.tsx` — calendar primitive ที่ใช้ใน CreatePlan
- [ ] `src/app/components/ui/card.tsx` — card layout ที่ใช้หลายหน้า
- [ ] `src/app/components/ui/checkbox.tsx` — checkbox primitive
- [ ] `src/app/components/ui/dialog.tsx` — modal dialog primitive
- [ ] `src/app/components/ui/input.tsx` — input primitive
- [ ] `src/app/components/ui/label.tsx` — label primitive
- [ ] `src/app/components/ui/popover.tsx` — popover primitive สำหรับ calendar
- [ ] `src/app/components/ui/progress.tsx` — progress bar ในหน้าแปลงนา
- [ ] `src/app/components/ui/select.tsx` — select/dropdown ใน calendar และ form
- [ ] `src/app/components/ui/utils.ts` — helper รวม className เช่น `cn`

## 16. สรุปลำดับอ่านแบบเร็ว

- [ ] รอบที่ 1: `config.py`, `database.py`, `security.py`, `dependencies.py` — รู้พื้นฐาน backend
- [ ] รอบที่ 2: models + schemas — รู้ว่า DB และ API หน้าตาเป็นอย่างไร
- [ ] รอบที่ 3: `plan_service.py`, `plans.py`, `varieties.py` — เข้าใจระบบวางแผนข้าว
- [ ] รอบที่ 4: `rag_service.py`, `chat.py`, `documents.py` — เข้าใจระบบ RAG
- [ ] รอบที่ 5: `api.ts`, `auth.ts`, `routes.tsx`, `PlansContext.tsx` — เข้าใจ frontend core
- [ ] รอบที่ 6: `CreatePlan.tsx`, `Plots.tsx`, `PlotDashboard.tsx`, `Calendar.tsx` — เข้าใจ user flow
- [ ] รอบที่ 7: `FloatingChat.tsx`, `Admin.tsx`, `VarietiesAdminPanel.tsx` — เข้าใจ chat/admin

## 17. จุดที่เอกสารเก่าต้องจำว่าเปลี่ยนแล้ว

- [ ] `RETRIEVAL_K` ปัจจุบัน default เป็น 5 ไม่ใช่ hardcoded 3
- [ ] frontend/backend ข้าวไวแสงใช้เดือน มิ.ย.-ก.ค. ตรงกันแล้ว
- [ ] `fert1_formula` ไม่อยู่ใน UI/API แล้ว เหลือ legacy DB/internal เท่านั้น
- [ ] label ปุ๋ยเปลี่ยนเป็น “ช่วงแตกกอ” และ “ช่วงกำเนิดช่อดอก”
- [ ] frontend มี admin route guard แล้ว
- [ ] unused UI components/dependencies ถูกลบออกแล้ว
- [ ] backend requirements ตัด `alembic` และ `psutil` ออกแล้ว

## 18. Mental Model ที่ต้องตอบให้ได้

- [ ] Backend คือ source of truth ของ validation, DB, plan generation, permission
- [ ] Frontend คือ interaction layer สำหรับ wizard, dashboard, checklist, calendar, admin
- [ ] แผนปลูกสร้างจาก rule-based logic ไม่ใช่ AI
- [ ] RAG ใช้ตอบคำถามและอธิบาย ไม่ได้ใช้สร้างแผน
- [ ] progress percent คือเวลาของ crop cycle
- [ ] checklist คือการ track ว่างานจริงทำเสร็จหรือยัง
- [ ] แผนเป็น baseline schedule ถ้างานจริงช้า task จะกลายเป็น overdue และติ๊กย้อนหลังได้
