# Rice Expert Demo Script

## Golden Rule

อย่าถามคำถามสดหน้า defense ถ้าไม่เคยทดสอบมาก่อน ให้ใช้คำถาม locked ที่มีเอกสารรองรับและรู้ expected behavior แล้วเท่านั้น

## Locked Demo Checklist

ก่อนเริ่ม demo:

- Backend server เปิดอยู่ที่ `http://localhost:8000`
- Frontend server เปิดอยู่
- PostgreSQL ใช้ database ที่มี demo data
- `.env` มี `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_EMBEDDING_MODEL`
- ChromaDB มีเอกสารใน collection `general` และ collection ของพันธุ์ข้าวที่ใช้ demo
- มี user, admin, พันธุ์ข้าว, เอกสาร, แผนปลูก, และ task ที่เคย tick แล้วอย่างน้อย 1 งาน

## Locked Demo Questions

ใช้ชุดนี้เป็น template แล้วแทนชื่อพันธุ์/ตัวเลขให้ตรงกับเอกสารจริงในเครื่อง:

1. RAG exact fact:
   - ถาม: "ข้าวขาวดอกมะลิ 105 เก็บเกี่ยวประมาณช่วงไหน"
   - Expected: ตอบจากเอกสารว่าประมาณช่วง 25 พฤศจิกายน พร้อม source

2. RAG vs No-RAG:
   - ถาม RAG และ No-RAG ด้วยคำถามเดียวกันที่เอกสารมีคำตอบเฉพาะ
   - Expected: RAG อ้างอิงเอกสารชัดกว่า ส่วน No-RAG มีโอกาสตอบกว้างหรือไม่ตรง source

3. Out-of-scope:
   - ถาม: "ราคาทองวันนี้ควรซื้อไหม"
   - Expected: ระบบ RAG ไม่ควรเดา และควรบอกว่าไม่มีข้อมูลเกี่ยวข้องในเอกสาร

4. Plot context:
   - ถามจากหน้า plot dashboard: "จากแปลงนี้ วันนี้ควรทำอะไร และงานถัดไปคืออะไร"
   - Expected: คำตอบใช้บริบทแปลง เช่น พันธุ์ข้าว ชนิดดิน stage งานวันนี้ และงานถัดไป

5. Fertilizer explanation:
   - ถาม: "ทำไมสูตรปุ๋ยช่วงแตกกอกับช่วงกำเนิดช่อดอกถึงมาจากคนละที่"
   - Expected: แตกกอเลือกตามดิน ส่วนกำเนิดช่อดอกใช้ `fert2_formula` จากพันธุ์ข้าว

## Manual Demo Flow

1. Guest opens landing page.
   Expected: Shows system intro, supported rice varieties, AI chat, and public knowledge documents.

2. Guest asks AI a basic rice question.
   Expected: AI answers in Thai. Explain that login is needed to save chat history and create plans.

3. User registers or logs in.
   Expected: Redirects to `/app/plots`.

4. User creates a plan.
   Use: select rice variety, choose valid start date, fill plot name, area, soil type, and planting method.
   Expected: Plan is created and appears in the plots list.

5. User opens plot dashboard.
   Expected: Shows current crop stage, time-based progress, resources, fertilizer formulas, and task checklist.
   Explain: Fertilizer during tillering is selected from soil type; fertilizer during panicle initiation comes from the rice variety.

6. User ticks a task.
   Expected: Task changes to completed and remains completed after page refresh because it is saved in `plan_tasks.is_completed`.

7. User edits plot area or soil type.
   Expected: Seed/fertilizer resources recalculate, while task list and completed status remain unchanged.

8. User opens calendar.
   Expected: Calendar marks dates that have tasks and shows task details for the selected date.

9. User asks floating AI chat about the current plot.
   Expected: AI receives plan context such as variety, soil, stage, today tasks, and upcoming tasks.

10. User clones the plan.
    Expected: New plan is generated from a new start date using the same variety, method, area, and soil.

11. Admin logs in.
    Expected: Admin sees the system management menu. Normal users cannot open `/app/admin` directly.

12. Admin manages rice varieties.
    Expected: Required fields validate before saving. Fertilizer during tillering uses soil automatically; fertilizer during panicle initiation uses the variety formula.

13. Admin uploads knowledge documents.
    Expected: Documents are grouped by collection and used by RAG after ingestion.

14. Admin manages prompt templates and knowledge gaps.
    Expected: Templates appear as suggested questions; gaps show questions with weak/no document support.

## Explanation For Committee

The generated plan is a baseline schedule, not a rigid real-world command. Rice farming can be delayed by rain, water availability, labor, pests, or field conditions.

The system separates two kinds of tracking:

- Time progress: the circular percentage shows where the plan should be in the crop cycle based on dates.
- Work completion: the checklist records whether each task was actually done and persists it in the database.

If real work is delayed, unfinished past tasks appear as overdue. The user can tick them when completed. If the whole production cycle needs to move, the user can clone or create a new plan from a new start date.

## Short Defense Answers

Architecture:

> Frontend React ส่ง request ไป backend FastAPI โดย backend จัดการ auth, RAG chat, document ingestion และ planting plan generation ข้อมูล structured เก็บใน PostgreSQL ส่วนเอกสารความรู้เก็บเป็น embedding ใน ChromaDB แล้วใช้ Gemini ผ่าน LangChain เพื่อสร้างคำตอบพร้อม source และ metrics

Why rule-based planning:

> แผนปลูกเป็น rule-based เพราะงานนี้ต้องการผลลัพธ์ที่ตรวจสอบได้และทำซ้ำได้ ไม่ควรให้ LLM เดาตารางงานหรือปริมาณทรัพยากรเอง

RAG value:

> RAG ช่วยให้คำตอบอิงเอกสารจริง ลด hallucination และแสดง source ได้ แม้ response time จะมากกว่า No-RAG เล็กน้อย

Fertilizer logic:

> สูตรปุ๋ยช่วงแตกกอเลือกจากชนิดดิน ส่วนสูตรช่วงกำเนิดช่อดอกใช้ค่าจากข้อมูลพันธุ์ข้าว (`fert2_formula`) แล้วบันทึกไว้ใน `resources_snapshot`
