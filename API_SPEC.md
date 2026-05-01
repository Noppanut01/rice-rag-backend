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
Backend generate tasks/resources จากพันธุ์ข้าว วิธีปลูก พื้นที่ และชนิดดิน

**Request**
```json
{
  "plot_name": "string | null",
  "variety_id": "string",
  "start_date": "YYYY-MM-DD",
  "area_rai": 0.0,
  "planting_method": "transplant | broadcast | throw",
  "soil_type": "clay | loam | sandy"
}
```

**Response 200**
```json
{
  "id": "uuid",
  "variety_id": "string",
  "variety_name": "string",
  "start_date": "string",
  "actual_planting_date": "string",
  "area_rai": 0.0,
  "plot_name": "string | null",
  "planting_method": "transplant",
  "soil_type": "clay",
  "is_photoperiod_sensitive": false,
  "resources": {
    "seed_kg": 0.0,
    "fertilizer1_kg": 0.0,
    "fertilizer1_formula": "16-20-0",
    "fertilizer2_kg": 0.0,
    "fertilizer2_formula": "46-0-0",
    "seedling_trays": null
  },
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

หมายเหตุ:
- `fertilizer1_formula` เลือกจาก `soil_type`: `clay` = `16-20-0`, `loam`/`sandy` = `16-16-8`
- `fertilizer2_formula` มาจากข้อมูลพันธุ์ข้าว

**Error**
- `401` — ไม่ได้ login
- `400` — วิธีปลูกไม่รองรับ, ข้อมูลพันธุ์ไม่ครบ, หรือช่วงปลูกข้าวไวแสงไม่เหมาะสม
- `404` — ไม่พบพันธุ์ข้าว

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

## PATCH /plans/{plan_id}

แก้ชื่อแปลง พื้นที่ หรือชนิดดิน — ต้อง login เจ้าของแผน
ถ้าแก้ `area_rai` หรือ `soil_type` จะคำนวณ `resources` ใหม่ แต่ไม่ล้าง tasks/checklist

**Request**
```json
{
  "plot_name": "string | null",
  "area_rai": 0.0,
  "soil_type": "clay | loam | sandy"
}
```

**Response 200** — PlanResponse

**Error**
- `400` — พื้นที่ต้องมากกว่า 0 หรือชนิดดินไม่ถูกต้อง
- `404` — ไม่พบแผน

---

## POST /plans/{plan_id}/clone

คัดลอกแผนเดิมโดยใช้วันเริ่มต้นใหม่ — ต้อง login เจ้าของแผน

**Request**
```json
{
  "start_date": "YYYY-MM-DD",
  "plot_name": "string | null"
}
```

**Response 200** — PlanResponse ใหม่ พร้อม tasks/resources ที่ generate จากวันเริ่มต้นใหม่

**Error**
- `400` — ข้อมูลพันธุ์/ช่วงปลูกไม่ถูกต้อง
- `404` — ไม่พบแผนต้นฉบับ หรือพันธุ์ข้าวไม่พร้อมใช้งาน

---

## DELETE /plans/{plan_id}

ลบแผนพร้อม tasks ทั้งหมด — ต้อง login เจ้าของแผนเท่านั้น

**Response 204** — No Content

**Error**
- `404` — ไม่พบแผน

---

## GET /varieties/

ดูพันธุ์ข้าวที่ active อยู่ — public

**Response 200**
```json
[
  {
    "id": "uuid",
    "name": "string",
    "collection_name": "string",
    "harvest_age_days": 120,
    "is_photoperiod_sensitive": false,
    "is_active": true,
    "supported_methods": ["transplant", "broadcast"],
    "description": "string | null",
    "reference_url": "string | null",
    "tillering_day": 25,
    "panicle_initiation_day": 55,
    "heading_day": 80,
    "fert1_rate": 20.0,
    "fert2_rate": 10.0,
    "fert2_formula": "46-0-0",
    "fert1_note": "string | null",
    "fert2_note": "string | null"
  }
]
```

`fert1_formula` ไม่ expose ใน API แล้ว เพราะสูตรช่วงแตกกอคำนวณจากชนิดดินของแผน

---

## POST /varieties/

สร้างพันธุ์ข้าว — ต้องเป็น admin

**Request**
```json
{
  "name": "string",
  "collection_name": "string",
  "harvest_age_days": 120,
  "is_photoperiod_sensitive": false,
  "supported_methods": ["transplant", "broadcast"],
  "tillering_day": 25,
  "panicle_initiation_day": 55,
  "heading_day": 80,
  "fert1_rate": 20.0,
  "fert2_rate": 10.0,
  "fert2_formula": "46-0-0",
  "description": "string | null",
  "reference_url": "string | null",
  "fert1_note": "string | null",
  "fert2_note": "string | null"
}
```

**Response 200** — RiceVarietyResponse

**Error**
- `400` — collection ซ้ำ/รูปแบบไม่ถูกต้อง, ระยะการเจริญเติบโตไม่เรียงลำดับ, หรือข้อมูลปุ๋ยไม่ครบ
- `403` — ไม่ใช่ admin

---

## PUT /varieties/{variety_id}

แก้พันธุ์ข้าว — ต้องเป็น admin

**Request** — ส่งเฉพาะ field ที่ต้องการแก้ได้ โครงสร้างเหมือน `POST /varieties/`

**Response 200** — RiceVarietyResponse

**Error**
- `400` — validation ไม่ผ่าน
- `403` — ไม่ใช่ admin
- `404` — ไม่พบพันธุ์ข้าว

---

## GET /varieties/{variety_id}/stats

ดูจำนวนเอกสารที่ผูกกับ collection ของพันธุ์ข้าว — ต้องเป็น admin

**Response 200**
```json
{
  "doc_count": 0,
  "collection_name": "string"
}
```

---

## DELETE /varieties/{variety_id}

ลบพันธุ์ข้าวพร้อมเอกสารใน collection นั้น — ต้องเป็น admin

**Response 200**
```json
{
  "detail": "ลบพันธุ์ข้าว 'string' และเอกสารที่เกี่ยวข้องทั้งหมดเรียบร้อย"
}
```

**Error**
- `403` — ไม่ใช่ admin
- `404` — ไม่พบพันธุ์ข้าว

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
| GET /varieties/ | ✅ | ✅ | ✅ |
| POST /varieties/ | ❌ | ❌ | ✅ |
| PUT /varieties/{id} | ❌ | ❌ | ✅ |
| GET /varieties/{id}/stats | ❌ | ❌ | ✅ |
| DELETE /varieties/{id} | ❌ | ❌ | ✅ |
| GET /documents/collections | ✅ | ✅ | ✅ |
| GET /documents/ | ✅ | ✅ | ✅ |
| GET /documents/{id}/file | ✅ | ✅ | ✅ |
| POST /documents/upload | ❌ | ❌ | ✅ |
| DELETE /documents/{id} | ❌ | ❌ | ✅ |
| POST /plans/ | ❌ | ✅ | ✅ |
| GET /plans/ | ❌ | ✅ | ✅ |
| PATCH /plans/{id} | ❌ | ✅ | ✅ |
| PATCH /plans/.../toggle | ❌ | ✅ | ✅ |
| POST /plans/{id}/clone | ❌ | ✅ | ✅ |
| DELETE /plans/{id} | ❌ | ✅ | ✅ |
| GET /prompts/ | ✅ | ✅ | ✅ |
| POST /prompts/ | ❌ | ❌ | ✅ |
| POST /prompts/generate | ❌ | ❌ | ✅ |
| DELETE /prompts/{id} | ❌ | ❌ | ✅ |
| GET /admin/faq | ❌ | ❌ | ✅ |
| GET /admin/gaps | ❌ | ❌ | ✅ |
| GET /admin/users | ❌ | ❌ | ✅ |
| PUT /admin/users/{id}/role | ❌ | ❌ | ✅ |

user ธรรมดา register แล้วได้ role = "user" อัตโนมัติ
การเปลี่ยน role เป็น admin ต้องแก้ตรง DB โดยตรง (ไม่มี endpoint)
