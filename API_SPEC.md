# Rice Farming RAG — API Specification

Base URL: `http://localhost:8000`

## Auth

ทุก endpoint ที่ต้องการ login ให้ส่ง header:
```
Authorization: Bearer <access_token>
```

---

## POST /auth/register

สมัครสมาชิก

**Request**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response 200**
```json
{
  "id": "uuid",
  "username": "string",
  "role": "user"
}
```

**Error**
- `400` — username ซ้ำ

---

## POST /auth/login

เข้าสู่ระบบ — รับ JSON (ไม่ใช่ form-data)

**Request**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response 200**
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

JWT payload มี field: `sub` (username), `role` ("user" | "admin")

**Error**
- `401` — username หรือ password ผิด

---

## POST /chat/

ถามคำถามผ่าน RAG — ต้อง login

**Request**
```json
{
  "question": "string"
}
```

**Response 200**
```json
{
  "answer": "string",
  "sources": ["string"],
  "response_time_ms": 0,
  "ram_used_mb": 0.0,
  "model_used": "string",
  "embedding_model": "string",
  "retrieval_strategy": "string",
  "chunk_size": 0,
  "chunks_retrieved": 0
}
```

**Error**
- `401` — ไม่ได้ login

---

## GET /chat/history

ดูประวัติการถามของ user ที่ login อยู่ — ต้อง login

**Response 200**
```json
[
  {
    "id": "uuid",
    "question": "string",
    "answer": "string",
    "model_used": "string",
    "created_at": "string"
  }
]
```

---

## POST /plans/

สร้างแผนการปลูกข้าวด้วย RAG — ต้อง login

**Request**
```json
{
  "variety_name": "string",
  "start_date": "YYYY-MM-DD",
  "area_rai": 0.0,
  "plot_name": "string | null"
}
```

**Response 200**
```json
{
  "id": "uuid",
  "variety_name": "string",
  "start_date": "string",
  "area_rai": 0.0,
  "plot_name": "string | null",
  "plan_content": {
    "answer": "string",
    "sources": ["string"]
  },
  "created_at": "string"
}
```

**Error**
- `401` — ไม่ได้ login

---

## GET /plans/

ดูแผนทั้งหมดของ user ที่ login อยู่ — ต้อง login

**Response 200** — array ของ PlanResponse (โครงสร้างเดียวกับ POST /plans/)

---

## GET /prompts/

ดึง prompt templates ทั้งหมด — ไม่ต้อง login (public)

**Response 200**
```json
[
  {
    "id": "uuid",
    "title": "string",
    "content": "string",
    "created_at": "string"
  }
]
```

---

## POST /prompts/

สร้าง prompt template — ต้องเป็น admin

**Request**
```json
{
  "title": "string",
  "content": "string"
}
```

**Response 201** — PromptTemplateResponse (โครงสร้างเดียวกับ GET /prompts/)

**Error**
- `403` — ไม่ใช่ admin

---

## DELETE /prompts/{template_id}

ลบ prompt template — ต้องเป็น admin

**Response 204** — No Content

**Error**
- `403` — ไม่ใช่ admin
- `404` — ไม่พบ template

---

## GET /documents/

ดูเอกสารทั้งหมดในระบบ — ต้องเป็น admin

**Response 200**
```json
[
  {
    "id": "uuid",
    "filename": "string",
    "file_type": "pdf | txt | docx",
    "chroma_collection": "string",
    "created_at": "string"
  }
]
```

---

## POST /documents/upload

อัปโหลดเอกสารเข้า vector store — ต้องเป็น admin

**Request** — multipart/form-data
```
files: File[]   (รองรับ .pdf .txt .docx, ส่งได้หลายไฟล์พร้อมกัน)
```

**Response 200** — array ของ DocumentResponse (โครงสร้างเดียวกับ GET /documents/)

**Error**
- `400` — นามสกุลไฟล์ไม่รองรับ
- `403` — ไม่ใช่ admin

---

## DELETE /documents/{id}

ลบเอกสารจาก DB และ vector store — ต้องเป็น admin

**Response 204** — No Content

**Error**
- `403` — ไม่ใช่ admin
- `404` — ไม่พบเอกสาร

---

## GET /admin/faq

ดู 10 คำถามที่ถูกถามบ่อยที่สุด — ต้องเป็น admin

**Response 200**
```json
[
  {
    "question": "string",
    "count": 0
  }
]
```

---

## Role

| Role | สิทธิ์ |
|------|--------|
| `user` | chat, plans, ดู prompts |
| `admin` | ทุกอย่าง + จัดการ documents, prompts, ดู faq |

user ธรรมดา register แล้วได้ role = "user" อัตโนมัติ
การเปลี่ยน role เป็น admin ต้องแก้ตรง DB โดยตรง (ไม่มี endpoint)
