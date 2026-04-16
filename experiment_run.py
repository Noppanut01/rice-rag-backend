"""
RAG Experiment Runner
usage: python3 experiment_run.py --run <run_id> --user <username> --password <password>
example: python3 experiment_run.py --run run1 --user run1 --password run1pass
"""

import argparse
import csv
import json
import time
from datetime import datetime
from pathlib import Path

import requests

BASE_URL = "http://localhost:8000"

PLAN_CONTEXT = """[บริบทแปลงนาของผู้ใช้]
พันธุ์: กข43
ลักษณะพันธุ์: ไม่ไวต่อช่วงแสง
วิธีปลูก: นาดำ
พื้นที่: 5.0 ไร่
ประเภทดิน: clay
วันที่เริ่มแผน: 2026-04-15
ผ่านมาแล้ว: 0 วัน
ระยะปัจจุบัน: เตรียมกล้า
งานวันนี้:
- ไถดะ: ไถพลิกดินครั้งแรก ตากดินไว้ 7 วัน เพื่อกำจัดวัชพืช เชื้อโรค และระบายก๊าซพิษออกจากดิน
- เพาะกล้า: แช่เมล็ดพันธุ์ 24 ชม. หุ้มเมล็ดในกระสอบ 30-48 ชม. จนงอกขนาดตุ่มตา แล้วหว่านในแปลงกล้า อัตรา 5-7 กก./ไร่
งานใน 7 วันข้างหน้า:
- ดูแลแปลงกล้า (รายวัน) (2026-04-16): รดน้ำเช้า-เย็นทุกวัน และตรวจเช็คความแข็งแรงของต้นกล้าจนกว่าจะถึงวันปักดำ
- ไถแปร (2026-04-22): ไถย่อยดินครั้งที่สอง คลุกเคล้าฟางข้าวและอินทรียวัตถุให้สลายตัว เตรียมพื้นดินสำหรับทำเทือก"""

# ชุดที่ 1 — ความรู้ทั่วไป (ไม่ใช้ plan_context)
QUESTIONS_SET1 = [
    "ข้าว กข43 นี่มันต่างจากข้าวหอมมะลิ 105 ยังไง เห็นเค้าว่าปลูกแป๊บเดียวก็ได้เกี่ยวแล้ว?",
    "ที่ว่า กข43 เป็นข้าวไม่ไวแสง หมายความว่าผมจะปลูกตอนไหนของปีก็ได้ใช่ไหม?",
    "จุดเด่นของข้าวพันธุ์นี้ที่เค้าเอาไปขายคนรักสุขภาพคืออะไร เห็นคนพูดกันเยอะ?",
    "ข้าว กข43 ปกติเค้าเกี่ยวกันตอนอายุกี่วันหลังจากหว่านหรือปักดำ?",
    "ถ้าที่นาผมมีนกกับหนูเยอะ ทำไมถึงต้องระวังเป็นพิเศษถ้าจะปลูก กข43?",
    "พันธุ์ กข43 นี่ต้นมันสูงแค่ไหน ล้มง่ายไหมถ้าประโคมใส่ปุ๋ยเยอะๆ?",
    "สภาพพื้นที่แบบไหนที่เหมาะกับ กข43 ที่สุด ถ้าเป็นนาอาศัยน้ำฝนอย่างเดียวจะรอดไหม?",
    "ถ้าเอาข้าว กข43 ไปหุงกิน รสชาติมันจะเป็นยังไง นุ่มเหมือนหอมมะลิไหม?",
    "ข้าวพันธุ์นี้ทนโรคไหม โดยเฉพาะพวกโรคไหม้กับเพลี้ยกระโดดสีน้ำตาล?",
    "ทำไมต้องมีระยะพักตัวของเมล็ดพันธุ์ 5 สัปดาห์ก่อนเอามาปลูกล่ะ?",
]

# ชุดที่ 2 — อ้างอิงบริบทแปลงนา (ใช้ plan_context)
QUESTIONS_SET2 = [
    "วันนี้ผมเริ่มไถดะแล้ว ต้องตากดินไว้นานแค่ไหนถึงจะดีที่สุดตามแผนที่วางไว้?",
    "นาผม 5 ไร่เป็นดินเหนียว จะเริ่มแผนปลูกวันนี้ (15 เม.ย.) ต้องเตรียมเมล็ดพันธุ์ทั้งหมดกี่กิโลถึงจะพอปักดำ?",
    "ช่วง 7 วันนี้ที่ผมดูแลแปลงกล้า ต้องรดน้ำยังไงบ้าง ต้นกล้าถึงจะแข็งแรงพร้อมปักดำ?",
    "ทำไมในแผนบอกว่าต้องไถแปรวันที่ 22 เม.ย. ล่ะ ไถดะเสร็จแล้วทำเทือกเลยไม่ได้เหรอ?",
    "เห็นว่า กข43 ลำต้นเล็ก แล้วนาผมเป็นดินเหนียวแบบนี้ ตอนใส่ปุ๋ยต้องระวังเรื่องข้าวล้มยังไง?",
    "การหุ้มเมล็ดพันธุ์ 30-48 ชม. จนงอก 'ตุ่มตา' มันมีหน้าตาเป็นยังไง แล้วทำไมต้องรอให้งอกเท่านี้?",
    "ถ้าช่วงตากดิน 7 วันนี้เกิดฝนตกหนัก แผนไถแปรของผมต้องเลื่อนออกไปไหม?",
    "ในแปลงนา 5 ไร่นี้ ถ้าผมเจอวัชพืชระบาดช่วงที่ตากดินอยู่ ต้องจัดการยังไงก่อนไถแปร?",
    "ดินเหนียว (Clay) แบบบ้านผมเนี่ย มันช่วยเรื่องการเก็บกักน้ำสำหรับข้าว กข43 ได้ดีกว่าดินทรายไหม?",
    "งานวันนี้มีทั้งไถดะทั้งเพาะกล้า ถ้าผมคนเดียวทำไม่ทัน ควรให้ความสำคัญกับงานไหนก่อนดี?",
]


def login(username: str, password: str) -> str:
    r = requests.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
    r.raise_for_status()
    return r.json()["access_token"]


def send_question(question: str, plan_context: str | None, token: str, use_rag: bool = True) -> dict:
    endpoint = "/chat/" if use_rag else "/chat/no-rag"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "question": question,
        "plan_context": plan_context,
        "collection": "rd43",
        "history": [],
    }
    r = requests.post(f"{BASE_URL}{endpoint}", json=payload, headers=headers)
    r.raise_for_status()
    return r.json()


def get_config() -> dict:
    """อ่าน config ปัจจุบันจาก .env ผ่าน backend"""
    r = requests.get(f"{BASE_URL}/docs/openapi.json")
    # อ่าน .env โดยตรง
    env = {}
    try:
        with open(".env") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    except Exception:
        pass
    return {
        "chunk_size": env.get("CHUNK_SIZE", "?"),
        "chunk_overlap": env.get("CHUNK_OVERLAP", "?"),
        "retrieval_k": env.get("RETRIEVAL_K", "?"),
        "retrieval_strategy": env.get("RETRIEVAL_STRATEGY", "?"),
        "temperature": env.get("LLM_TEMPERATURE", "?"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, help="run id เช่น run1")
    parser.add_argument("--user", required=True, help="username")
    parser.add_argument("--password", required=True, help="password")
    parser.add_argument("--no-rag", action="store_true", help="ใช้ no-rag endpoint (สำหรับ run11)")
    args = parser.parse_args()

    print(f"\n{'='*50}")
    print(f"RAG Experiment — {args.run}")
    print(f"{'='*50}")

    # อ่าน config
    config = get_config()
    print(f"Config: {json.dumps(config, ensure_ascii=False)}")

    # login
    print(f"\nLogging in as {args.user}...")
    token = login(args.user, args.password)
    print("Login OK")

    results = []
    use_rag = not args.no_rag

    # ชุดที่ 1 — ไม่ใช้ plan_context
    print(f"\n--- ชุดที่ 1: ความรู้ทั่วไป (no plan_context) ---")
    for i, q in enumerate(QUESTIONS_SET1, 1):
        print(f"[{i}/20] {q[:50]}...")
        data = send_question(q, None, token, use_rag)
        results.append({
            "run_id": args.run,
            "set": 1,
            "q_no": i,
            "question": q,
            "answer": data["answer"],
            "chunks_retrieved": data["chunks_retrieved"],
            "input_tokens": data["input_tokens"],
            "output_tokens": data["output_tokens"],
            "response_time_ms": data["response_time_ms"],
            "retrieval_strategy": data["retrieval_strategy"],
            "chunk_size": data["chunk_size"],
            "retrieval_k": data["retrieval_k"],
            **config,
        })
        time.sleep(1)

    # ชุดที่ 2 — ใช้ plan_context
    print(f"\n--- ชุดที่ 2: อ้างอิงแปลงนา (with plan_context) ---")
    for i, q in enumerate(QUESTIONS_SET2, 1):
        print(f"[{i+10}/20] {q[:50]}...")
        data = send_question(q, PLAN_CONTEXT, token, use_rag)
        results.append({
            "run_id": args.run,
            "set": 2,
            "q_no": i + 10,
            "question": q,
            "answer": data["answer"],
            "chunks_retrieved": data["chunks_retrieved"],
            "input_tokens": data["input_tokens"],
            "output_tokens": data["output_tokens"],
            "response_time_ms": data["response_time_ms"],
            "retrieval_strategy": data["retrieval_strategy"],
            "chunk_size": data["chunk_size"],
            "retrieval_k": data["retrieval_k"],
            **config,
        })
        time.sleep(1)

    # บันทึก CSV
    out_dir = Path("experiment_results")
    out_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"{args.run}_{ts}.csv"

    fieldnames = ["run_id", "set", "q_no", "question", "answer",
                  "chunks_retrieved", "input_tokens", "output_tokens", "response_time_ms",
                  "chunk_size", "chunk_overlap", "retrieval_k", "retrieval_strategy", "temperature"]

    with open(out_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    # รายงาน
    print(f"\n{'='*50}")
    print(f"REPORT — {args.run}")
    print(f"{'='*50}")
    print(f"ไฟล์ผลลัพธ์: {out_file}")
    print(f"คำถามทั้งหมด: {len(results)} ข้อ")
    avg_time = sum(r["response_time_ms"] for r in results) / len(results)
    avg_input = sum(r["input_tokens"] for r in results) / len(results)
    avg_output = sum(r["output_tokens"] for r in results) / len(results)
    avg_chunks = sum(r["chunks_retrieved"] for r in results) / len(results)
    print(f"avg response_time_ms : {avg_time:.0f} ms")
    print(f"avg input_tokens     : {avg_input:.0f}")
    print(f"avg output_tokens    : {avg_output:.0f}")
    print(f"avg chunks_retrieved : {avg_chunks:.1f}")
    print(f"\nคำตอบทั้งหมด:")
    for r in results:
        print(f"\nQ{r['q_no']} (set{r['set']}): {r['question']}")
        print(f"A: {r['answer'][:120]}...")


if __name__ == "__main__":
    main()
