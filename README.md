# Rice Farming RAG Backend

Backend สำหรับระบบผู้เชี่ยวชาญการปลูกข้าว — ใช้ RAG (Retrieval-Augmented Generation) ด้วย local LLM ผ่าน Ollama

**Thesis contribution**: เปรียบเทียบ local LLM บน RAG pipeline ว่า optimize แล้วต่างจากไม่ optimize แค่ไหน (เวลา, RAM, คุณภาพคำตอบ)

---

## Tech Stack

- **FastAPI** — REST API
- **PostgreSQL** — เก็บ users, chat history, plans, documents
- **SQLAlchemy** — ORM (ใช้ `create_all` ไม่ใช้ Alembic)
- **ChromaDB** — Vector store สำหรับ embeddings (single collection `rice_knowledge`)
- **LangChain** — RAG pipeline
- **Ollama** — รัน local LLM
  - LLM: `gemma3:4b` (prod) / `llama3.2:3b` (dev)
  - Embedding: `bge-m3` (prod) / `mxbai-embed-large` (dev)
- **JWT** — Authentication (python-jose + passlib)

---

## Requirements

- Python 3.12+
- PostgreSQL (Postgres.app หรือ Docker)
- [Ollama](https://ollama.com) พร้อม model ที่ต้องการ

```bash
ollama pull llama3.2:3b
ollama pull mxbai-embed-large
```

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
# แก้ DATABASE_URL และ SECRET_KEY

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

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_LLM_MODEL=llama3.2:3b
OLLAMA_EMBEDDING_MODEL=mxbai-embed-large

CHUNK_SIZE=500
CHUNK_OVERLAP=50
RETRIEVAL_STRATEGY=mmr
RETRIEVAL_K=3
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
| POST | `/plans/` | user | สร้างแผนการปลูกข้าว |
| GET | `/plans/` | user | ดูแผนทั้งหมดของตัวเอง |
| PATCH | `/plans/{id}/tasks/{task_id}/toggle` | user | toggle task เสร็จ/ยังไม่เสร็จ |
| DELETE | `/plans/{id}` | user | ลบแผน |
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

## Experiment Metrics

ทุก request บันทึก metrics ลง `chat_history` สำหรับเปรียบเทียบ:

- `response_time_ms` — เวลาตั้งแต่รับ query จนได้คำตอบ
- `ram_used_mb` — RAM ที่ใช้ระหว่าง generate
- `model_used`, `embedding_model`, `retrieval_strategy`, `chunk_size`, `chunks_retrieved`

ปรับ config ผ่าน `.env` เพื่อทำ experiment โดยไม่ต้องแก้ code

---

## Branch

- `main` — stable
- `dev` — main development branch
- `feature/rag-plan-generation` — RAG-based plan generation (TODO: รอ PDF documents)
