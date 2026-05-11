# Rice Farming RAG Backend

Backend สำหรับระบบผู้เชี่ยวชาญการปลูกข้าว — ใช้ RAG (Retrieval-Augmented Generation) ผ่าน Google Gemini API

**Thesis contribution**: เปรียบเทียบคำตอบของระบบ RAG กับ No-RAG ว่าแตกต่างกันแค่ไหนในด้านคุณภาพคำตอบ การลด hallucination และเวลาตอบสนอง

---

## Tech Stack

- **FastAPI** — REST API
- **PostgreSQL** — เก็บ users, chat history, plans, documents, rice varieties
- **SQLAlchemy** — ORM (ใช้ `create_all` ไม่ใช้ Alembic)
- **ChromaDB** — Vector store สำหรับ embeddings แยก collection ตามพันธุ์ข้าวและ `general`
- **LangChain** — RAG pipeline
- **Google Gemini API** — LLM และ embedding
  - LLM: `gemini-2.5-flash`
  - Embedding: `gemini-embedding-001`
- **JWT** — Authentication (python-jose + passlib)

---

## Requirements

- Python 3.12+
- PostgreSQL (Postgres.app หรือ Docker)
- Google AI Studio API key สำหรับ Gemini

---

## Setup

```bash
# 1. clone และเข้า directory
git clone <repo-url>
cd rice-rag-backend

# 2. สร้าง virtual environment
python -m venv venv
source venv/bin/activate

# 3. ติดตั้ง dependencies
pip install -r requirements.txt

# 4. สร้าง .env จาก template
cp .env.example .env
# แก้ DATABASE_URL, GEMINI_API_KEY และ SECRET_KEY

# 5. สร้าง database (รัน PostgreSQL ก่อน)
createdb ricerag

# 6. รัน server
uvicorn app.main:app --reload
```

Swagger docs: http://localhost:8000/docs

---

## Environment Variables

```env
DATABASE_URL=postgresql://user:password@localhost:5432/ricerag

GEMINI_API_KEY=your-google-ai-studio-api-key
GEMINI_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001

CHUNK_SIZE=500
CHUNK_OVERLAP=50
RETRIEVAL_STRATEGY=mmr
RETRIEVAL_K=5
LLM_TEMPERATURE=0.3

CHROMA_PERSIST_DIRECTORY=./chroma_db
UPLOAD_DIR=./uploads

SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

---

## API Overview

| Method | Endpoint | Auth | คำอธิบาย |
|--------|----------|------|---------|
| POST | `/auth/register` | — | สมัครสมาชิก |
| POST | `/auth/login` | — | เข้าสู่ระบบ รับ JWT token (JSON body) |
| POST | `/chat/` | optional | ถามคำถาม → RAG ตอบ (login → บันทึก history) |
| POST | `/chat/no-rag` | optional | ถามโดยไม่ใช้ RAG (สำหรับ experiment) |
| GET | `/chat/history` | user | ประวัติการถาม |
| GET | `/varieties/` | — | ดูพันธุ์ข้าวที่ active |
| POST | `/varieties/` | admin | เพิ่มพันธุ์ข้าว |
| PUT | `/varieties/{id}` | admin | แก้พันธุ์ข้าว |
| DELETE | `/varieties/{id}` | admin | ลบพันธุ์ข้าวและเอกสารที่เกี่ยวข้อง |
| POST | `/plans/` | user | สร้างแผนการปลูกข้าวจากพันธุ์ วิธีปลูก พื้นที่ และชนิดดิน |
| GET | `/plans/` | user | ดูแผนทั้งหมดของตัวเอง |
| PATCH | `/plans/{id}` | user | แก้ชื่อแปลง/พื้นที่/ชนิดดิน และคำนวณ resources ใหม่ |
| PATCH | `/plans/{id}/tasks/{task_id}/toggle` | user | toggle task เสร็จ/ยังไม่เสร็จ |
| POST | `/plans/{id}/clone` | user | คัดลอกแผนโดยใช้วันเริ่มต้นใหม่ |
| DELETE | `/plans/{id}` | user | ลบแผน |
| GET | `/documents/collections` | — | ดู collection สำหรับอัปโหลดเอกสาร |
| GET | `/documents/` | — | ดูเอกสารทั้งหมด |
| GET | `/documents/{id}/file` | — | เปิดอ่านไฟล์เอกสาร (PDF เปิดใน browser) |
| POST | `/documents/upload` | admin | อัปโหลดเอกสาร → embed เข้า ChromaDB |
| DELETE | `/documents/{id}` | admin | ลบเอกสาร |
| GET | `/prompts/` | — | ดู prompt templates |
| POST | `/prompts/` | admin | สร้าง prompt template |
| DELETE | `/prompts/{id}` | admin | ลบ prompt template |
| GET | `/admin/faq` | admin | top 10 คำถามที่ถามบ่อย |

ดูรายละเอียดทุก endpoint ได้ที่ [API_SPEC.md](./API_SPEC.md)

---

## Role & Access

| Role | สิทธิ์ |
|------|--------|
| guest (ไม่ login) | chat, ดูเอกสาร/อ่าน PDF, ดู prompts |
| `user` | ทุกอย่างของ guest + plans, chat history |
| `admin` | ทุกอย่าง + จัดการ documents/prompts, ดู FAQ |

สมัครใหม่ได้ role `user` อัตโนมัติ — เปลี่ยนเป็น admin ต้องแก้ DB โดยตรง

---

## Planting Plan Notes

- แผนปลูก generate tasks/resources ที่ backend จากข้อมูลพันธุ์ข้าว วิธีปลูก พื้นที่ และชนิดดิน
- สูตรปุ๋ยช่วงแตกกอ (`fertilizer1_formula`) เลือกตามดิน: `clay` = `16-20-0`, `loam`/`sandy` = `16-16-8`
- สูตรปุ๋ยช่วงกำเนิดช่อดอก (`fertilizer2_formula`) ใช้ค่าจากพันธุ์ข้าว (`fert2_formula`)
- `rice_varieties.fert1_formula` ยังอยู่เป็น legacy DB column แต่ไม่เปิดใน API/UI แล้ว

---

## Experiment Metrics

ทุก request บันทึก metrics ลง `chat_history` สำหรับเปรียบเทียบ:

- `response_time_ms` — เวลาตั้งแต่รับ query จนได้คำตอบ
- `model_used`, `embedding_model`, `retrieval_strategy`, `chunk_size`, `retrieval_k`, `chunks_retrieved`
- `input_tokens`, `output_tokens` — token usage จาก Gemini response metadata เมื่อมีข้อมูล

ปรับ config ผ่าน `.env` เพื่อทำ experiment โดยไม่ต้องแก้ code

---

## Branch

- `main` — stable
- `dev` — main development branch (current)
