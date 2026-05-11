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
Frontend decode JWT เอาเพื่อได้ username และ role โดยไม่ต้องเรียก /me

**Error**
- `401` — username หรือ password ผิด

---

## POST /chat/

ถามคำถามผ่าน RAG — **optional auth**
- ไม่ login → ตอบได้ แต่ไม่บันทึก history
- login → ตอบและบันทึก chat_history

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

---

## POST /chat/no-rag

ถามคำถามโดยไม่ใช้ RAG context — สำหรับ experiment เปรียบเทียบ
- ไม่บันทึก history
- optional auth

**Request / Response** — เหมือน `POST /chat/` ทุกอย่าง
- `retrieval_strategy` จะเป็น `"none"`
- `chunks_retrieved` จะเป็น `0`

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

สร้างแผนการปลูกข้าว — ต้อง login
Frontend generate tasks ด้วย planGenerator.ts แล้วส่งมาพร้อมกัน

> **TODO (feature/rag-plan-generation)**: เมื่อมี PDF พร้อมแล้ว
> จะเปลี่ยนให้ backend generate tasks ด้วย RAG แทน
> frontend จะส่งแค่ข้อมูลพื้นฐาน ไม่ส่ง tasks

**Request**
```json
{
  "plot_name": "string | null",
  "variety_id": "string",
  "variety_name": "string",
  "start_date": "YYYY-MM-DD",
  "area_rai": 0.0,
  "tasks": [
    {
      "day": 1,
      "stage": "string",
      "task_name": "string",
      "description": "string | null",
      "date": "YYYY-MM-DD"
    }
  ]
}
```

**Response 200**
```json
{
  "id": "uuid",
  "variety_id": "string",
  "variety_name": "string",
  "start_date": "string",
  "area_rai": 0.0,
  "plot_name": "string | null",
  "tasks": [
    {
      "id": "uuid",
      "day": 1,
      "stage": "string",
      "task_name": "string",
      "description": "string | null",
      "date": "string",
      "is_completed": false
    }
  ],
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

## PATCH /plans/{plan_id}/tasks/{task_id}/toggle

toggle task เสร็จ/ยังไม่เสร็จ — ต้อง login

**Response 200** — PlanTaskResponse (task ที่อัพเดตแล้ว)

**Error**
- `404` — ไม่พบแผนหรืองาน

---

## DELETE /plans/{plan_id}

ลบแผนพร้อม tasks ทั้งหมด — ต้อง login เจ้าของแผนเท่านั้น

**Response 204** — No Content

**Error**
- `404` — ไม่พบแผน

---

## GET /documents/

ดูเอกสารทั้งหมดในระบบ — **public** (ไม่ต้อง login)

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

## GET /documents/{id}/file

เปิดอ่านไฟล์เอกสารจริง — **public** (ไม่ต้อง login)

**Response** — ไฟล์ตาม media type (PDF เปิดใน browser, docx ดาวน์โหลด)

**Error**
- `404` — ไม่พบเอกสารหรือไฟล์

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

## GET /prompts/

ดึง prompt templates ทั้งหมด — public

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

**Response 201** — PromptTemplateResponse

**Error**
- `403` — ไม่ใช่ admin

---

## POST /prompts/generate

ให้ LLM สร้างตัวอย่างคำถามจากเอกสารในระบบ — ต้องเป็น admin

ดึง chunks จากทุก collection แล้วให้ LLM generate คำถาม 5 ข้อ (temperature=0.7)

**Response 200**
```json
[
  {
    "title": "string",
    "content": "string"
  }
]
```

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

## Role & Access

| endpoint | guest | user | admin |
|---|---|---|---|
| POST /chat/ | ✅ (ไม่บันทึก) | ✅ | ✅ |
| POST /chat/no-rag | ✅ | ✅ | ✅ |
| GET /chat/history | ❌ | ✅ | ✅ |
| GET /documents/ | ✅ | ✅ | ✅ |
| GET /documents/{id}/file | ✅ | ✅ | ✅ |
| POST /documents/upload | ❌ | ❌ | ✅ |
| DELETE /documents/{id} | ❌ | ❌ | ✅ |
| POST /plans/ | ❌ | ✅ | ✅ |
| GET /plans/ | ❌ | ✅ | ✅ |
| PATCH /plans/.../toggle | ❌ | ✅ | ✅ |
| DELETE /plans/{id} | ❌ | ✅ | ✅ |
| GET /prompts/ | ✅ | ✅ | ✅ |
| POST /prompts/ | ❌ | ❌ | ✅ |
| POST /prompts/generate | ❌ | ❌ | ✅ |
| DELETE /prompts/{id} | ❌ | ❌ | ✅ |
| GET /admin/faq | ❌ | ❌ | ✅ |

user ธรรมดา register แล้วได้ role = "user" อัตโนมัติ
การเปลี่ยน role เป็น admin ต้องแก้ตรง DB โดยตรง (ไม่มี endpoint)
