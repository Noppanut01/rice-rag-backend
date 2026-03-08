# Backend Plan — Rice Farming RAG Web App
> **พระเอกของ project คือ RAG** — ส่วนอื่นเป็น case study เพื่อให้เห็นภาพการใช้งานจริง

---

## Core Concept

```
User กรอก:                  ระบบทำ:
- พันธุ์ข้าว      ──►      Generate แผนการปลูกเบื้องต้น
- วิธีปลูก        ──►      RAG ให้ข้อมูล/ความรู้เพิ่มเติม
- วันเริ่มปลูก    ──►      User ถามลึกได้ผ่าน Chatbot
```

**Thesis contribution หลัก**: เปรียบเทียบ local LLM บน RAG pipeline
ว่า optimize แล้วต่างจากไม่ optimize แค่ไหน (เวลา, RAM, คุณภาพ)

---

## Tech Stack

| Layer | Tool | หมายเหตุ |
|-------|------|---------|
| Framework | FastAPI | async, auto Swagger docs |
| Database | PostgreSQL | เก็บ user, plan, chat history |
| ORM | SQLAlchemy + Alembic | migrations |
| Vector DB | ChromaDB | เก็บ embeddings ของเอกสาร |
| RAG | LangChain | orchestrate pipeline |
| LLM | Ollama (gemma3:4b / llama3.2:3b) | local model |
| Embedding | Ollama (bge-m3) | multilingual รองรับไทย |
| Auth | JWT (python-jose + passlib) | minimal |

---

## Project Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app + CORS + routers
│   ├── database.py              # PostgreSQL connection
│   ├── dependencies.py          # get_db, get_current_user, require_admin
│   │
│   ├── models/
│   │   ├── user.py              # User (id, email, password, role)
│   │   ├── document.py          # Document (RAG knowledge base)
│   │   ├── chat.py              # ChatHistory + metrics
│   │   └── plan.py              # PlantingPlan (simple)
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── document.py
│   │   └── plan.py
│   │
│   ├── routers/
│   │   ├── auth.py              # login, register, /me
│   │   ├── chat.py              # POST /chat (RAG), GET /chat/history
│   │   ├── documents.py         # Admin: upload/list/delete
│   │   └── plans.py             # User: สร้าง/ดูแผน
│   │
│   ├── services/
│   │   ├── rag_service.py       # RAG pipeline (พระเอก)
│   │   └── plan_service.py      # generate แผนจาก input
│   │
│   └── core/
│       ├── config.py            # .env settings (BaseSettings)
│       └── security.py          # JWT + bcrypt
│
├── .env
├── requirements.txt
└── alembic/
```

---

## Database Schema (Simplified)

### `users`
| column | type | note |
|--------|------|------|
| id | UUID PK | |
| email | VARCHAR UNIQUE | |
| hashed_password | VARCHAR | |
| full_name | VARCHAR | |
| role | ENUM('admin','user') | default 'user' |
| created_at | TIMESTAMP | |

### `documents`
| column | type | note |
|--------|------|------|
| id | UUID PK | |
| filename | VARCHAR | |
| file_path | VARCHAR | |
| chroma_collection | VARCHAR | collection name ใน ChromaDB |
| uploaded_by | UUID FK → users | Admin only |
| created_at | TIMESTAMP | |

### `prompt_templates`
| column | type | note |
|--------|------|------|
| id | UUID PK | |
| title | VARCHAR | ชื่อ template |
| content | TEXT | ข้อความคำถาม |
| created_by | UUID FK → users | Admin only |
| created_at | TIMESTAMP | |

### `chat_history`
> สำคัญมาก — เก็บ metrics สำหรับ experiment comparison

| column | type | note |
|--------|------|------|
| id | UUID PK | |
| user_id | UUID FK → users | NOT NULL (ต้อง login) |
| question | TEXT | |
| answer | TEXT | |
| sources | JSONB | `[{doc_id, title}]` |
| model_used | VARCHAR | เช่น `gemma3:4b-q4_K_M` |
| embedding_model | VARCHAR | เช่น `bge-m3` |
| retrieval_strategy | VARCHAR | `similarity` หรือ `mmr` |
| chunk_size | INT | |
| chunks_retrieved | INT | |
| response_time_ms | INT | เวลาตั้งแต่รับ query → ได้คำตอบ |
| ram_used_mb | FLOAT | RAM ที่ใช้ระหว่าง generate |
| created_at | TIMESTAMP | |

### `planting_plans`
| column | type | note |
|--------|------|------|
| id | UUID PK | |
| user_id | UUID FK → users | |
| variety_name | VARCHAR | ชื่อพันธุ์ข้าว |
| start_date | DATE | |
| area_rai | FLOAT | |
| plan_content | JSONB | แผนที่ generate มา |
| created_at | TIMESTAMP | |

---

## API Endpoints

### Auth (minimal)
```
POST  /auth/register     สมัครสมาชิก
POST  /auth/login        รับ JWT token
GET   /auth/me           ดูข้อมูลตัวเอง
```

### RAG Chat (พระเอก)
```
POST  /chat              ถามคำถาม → RAG ตอบ + บันทึก metrics
GET   /chat/history      ประวัติการสนทนา
```

### Documents (Admin only)
```
GET    /documents         list เอกสารทั้งหมด
POST   /documents/upload  อัปโหลด PDF/TXT/DOCX → chunk → embed
DELETE /documents/{id}    ลบเอกสาร + ChromaDB collection
```

### Plans (Case Study)
```
POST  /plans              กรอก variety + start_date → return แผน
GET   /plans              list แผนของ user
GET   /plans/{id}         ดูแผน
```

### Prompt Templates
```
GET    /prompts           list templates (ทุก user รวม anonymous)
POST   /prompts           admin สร้าง template ใหม่
DELETE /prompts/{id}      admin ลบ template
```

### Admin Analytics
```
GET   /admin/faq          top N คำถามที่ถูกถามบ่อย (aggregate chat_history)
```

### Misc
```
GET   /health             server + RAG status
```

---

## RAG Pipeline (Core)

```
User Question
     │
     ▼
FastAPI  POST /chat
     │
     ▼
RAGService.ask_question(question, config)
  ├─ 1. บันทึก start_time + RAM before
  ├─ 2. Embed question  →  bge-m3 (Ollama)
  ├─ 3. Retrieve chunks  →  ChromaDB
  │      ├─ similarity_search(k=3)       [baseline]
  │      └─ max_marginal_relevance(k=3)  [optimized]
  ├─ 4. Build context จาก top chunks
  ├─ 5. Generate answer  →  Ollama LLM
  └─ 6. บันทึก response_time_ms + RAM used
     │
     ▼
บันทึก chat_history (metrics ครบ) → PostgreSQL
     │
     ▼
Return answer + sources + metrics
```

---

## Optimization Experiments (Thesis Contribution)

### จุดที่ Optimize ได้

**1. Model Quantization**
```bash
ollama pull gemma3:4b           # default (Q4) — baseline
ollama pull gemma3:4b-q8_0     # Q8 — คุณภาพดีขึ้น RAM มากขึ้น
ollama pull llama3.2:3b         # เปรียบเทียบ model ต่างกัน
```

**2. Chunk Size & Overlap**
```python
# ทดลอง 3 แบบ
(chunk_size=500,  chunk_overlap=50)   # เล็ก → ดึงแม่น
(chunk_size=1000, chunk_overlap=200)  # กลาง → baseline
(chunk_size=1500, chunk_overlap=300)  # ใหญ่ → context เยอะ
```

**3. Retrieval Strategy**
```python
# Baseline
vectorstore.similarity_search(query, k=3)

# Optimized — ลด chunk ซ้ำ หลากหลายขึ้น
vectorstore.max_marginal_relevance_search(query, k=3, fetch_k=10)
```

**4. Embedding Model**
```bash
ollama pull mxbai-embed-large  # baseline (English-focused)
ollama pull bge-m3             # optimized (multilingual + ไทย)
```

**5. Response Caching**
```python
# ไม่มี cache → baseline
# มี cache → คำถามซ้ำไม่ต้อง compute ใหม่
from langchain.cache import InMemoryCache
```

---

### ตารางเปรียบเทียบ Experiments

| # | Model | Quant | Chunk | Retrieval | Embedding | Cache |
|---|-------|-------|-------|-----------|-----------|-------|
| **Baseline** | gemma3:4b | default | 1000/200 | similarity | mxbai | ❌ |
| Exp 1 | gemma3:4b | q8_0 | 1000/200 | similarity | mxbai | ❌ |
| Exp 2 | gemma3:4b | default | 500/50 | similarity | mxbai | ❌ |
| Exp 3 | gemma3:4b | default | 500/50 | MMR | mxbai | ❌ |
| Exp 4 | gemma3:4b | default | 500/50 | MMR | bge-m3 | ❌ |
| Exp 5 | gemma3:4b | default | 500/50 | MMR | bge-m3 | ✅ |
| Exp 6 | llama3.2:3b | default | 500/50 | MMR | bge-m3 | ✅ |
| **Best** | สรุปตัวที่ดีที่สุด | | | | | |

---

### Metrics ที่วัดทุก Request

```python
{
  "response_time_ms": 1240,
  "ram_used_mb": 312,
  "model_used": "gemma3:4b",
  "embedding_model": "bge-m3",
  "retrieval_strategy": "mmr",
  "chunk_size": 500,
  "chunks_retrieved": 3,
}
```

---

### Code โครง Experiment

```python
# services/rag_service.py
import time, psutil

def ask_question(self, question: str) -> dict:
    start = time.time()
    ram_before = psutil.Process().memory_info().rss / 1024 / 1024

    # Retrieve
    if self.retrieval_strategy == "mmr":
        docs = vs.max_marginal_relevance_search(question, k=self.k)
    else:
        docs = vs.similarity_search(question, k=self.k)

    # Generate
    answer = chain.invoke({"question": question, "context": context})

    ram_after = psutil.Process().memory_info().rss / 1024 / 1024

    return {
        "answer": answer,
        "response_time_ms": round((time.time() - start) * 1000),
        "ram_used_mb": round(ram_after - ram_before, 2),
        "model_used": self.llm_model,
        "retrieval_strategy": self.retrieval_strategy,
    }
```

---

## Build Order

### Phase 1 — Foundation
- [ ] `core/config.py` — BaseSettings จาก .env
- [ ] `database.py` — PostgreSQL + SessionLocal
- [ ] `models/` — ORM models ทั้งหมด
- [ ] Alembic migration → สร้าง tables

### Phase 2 — RAG Core (พระเอก)
- [ ] `services/rag_service.py` — pipeline ครบ พร้อม metrics
- [ ] `routers/documents.py` — upload/list/delete + auto embed
- [ ] `routers/chat.py` — /chat + บันทึก metrics ทุก request

### Phase 3 — Auth (Minimal)
- [ ] `core/security.py` — bcrypt + JWT
- [ ] `routers/auth.py` — register, login, /me
- [ ] `dependencies.py` — get_current_user, require_admin

### Phase 4 — Case Study
- [ ] `services/plan_service.py` — generate แผนจาก input
- [ ] `routers/plans.py` — CRUD planting plans

### Phase 5 — Admin Features (จาก Proposal)
- [ ] `models/prompt.py` — PromptTemplate model
- [ ] `schemas/prompt.py` — PromptTemplateRequest, PromptTemplateResponse
- [ ] `routers/prompts.py` — GET (all users), POST/DELETE (admin only)
- [ ] `routers/admin.py` — GET /admin/faq (aggregate chat_history)

---

## Dependencies (`requirements.txt`)

```
fastapi
uvicorn[standard]
sqlalchemy
alembic
psycopg2-binary
python-jose[cryptography]
passlib[bcrypt]
python-multipart
python-dotenv
pydantic-settings
langchain
langchain-ollama
langchain-chroma
langchain-community
pypdf
docx2txt
psutil
```

---

## Environment Variables (`.env`)

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ricerag

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_LLM_MODEL=gemma3:4b
OLLAMA_EMBEDDING_MODEL=bge-m3

# RAG Config (เปลี่ยนเพื่อทำ experiment)
CHUNK_SIZE=500
CHUNK_OVERLAP=50
RETRIEVAL_STRATEGY=mmr
RETRIEVAL_K=3
LLM_TEMPERATURE=0.3

# ChromaDB
CHROMA_PERSIST_DIRECTORY=./chroma_db

# Upload
UPLOAD_DIR=./uploads

# Auth
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

---

*อัปเดต: 2026-02-22*
*สรุป: RAG คือ thesis หลัก / App เป็น case study / วัด optimize vs baseline*
