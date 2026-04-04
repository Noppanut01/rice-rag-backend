from datetime import date, timedelta


def _build_tasks(planting_method: str, harvest_age_days: int, area_rai: float) -> list[dict]:
    f1 = round(25 * area_rai, 1)
    f2 = round(20 * area_rai, 1)

    if planting_method == "transplant":
        return [
            (-25, "เตรียมกล้า", "เพาะกล้า", "แช่เมล็ดพันธุ์ 24 ชม. แล้วเพาะในแปลงกล้า อัตรา 20-30 กก./ไร่"),
            (-7,  "เตรียมดิน", "ไถและคราดแปลงนา", "ไถดินลึก 15-20 ซม. คราดให้ละเอียด ปรับระดับดิน"),
            (0,   "ปักดำ", "ปักดำต้นกล้า", "ปักดำต้นกล้าอายุ 25 วัน ระยะ 20×20 ซม. 3-5 ต้นต่อกอ"),
            (20,  "ระยะแตกกอ", "ใส่ปุ๋ยครั้งที่ 1", f"ปุ๋ยสูตร 16-20-0 อัตรา 25 กก./ไร่ รวม {f1} กก. (ถามผู้ช่วย AI สำหรับคำแนะนำเฉพาะพันธุ์)"),
            (round(harvest_age_days * 0.5), "ระยะกำเนิดช่อดอก", "ใส่ปุ๋ยครั้งที่ 2", f"ปุ๋ยสูตร 46-0-0 อัตรา 20 กก./ไร่ รวม {f2} กก."),
            (round(harvest_age_days * 0.8), "ระยะออกรวง", "ตรวจสอบรวงข้าว", "สังเกตการออกรวง ตรวจโรคและแมลงศัตรูข้าว"),
            (harvest_age_days, "เก็บเกี่ยว", "เก็บเกี่ยวผลผลิต", "เก็บเกี่ยวเมื่อเมล็ดสุก 80% ของรวง"),
        ]

    if planting_method == "broadcast":
        h = harvest_age_days - 15
        seed = round(17 * area_rai, 1)
        return [
            (-7, "เตรียมดิน", "ไถและคราดแปลงนา", "ไถดินลึก 15-20 ซม. คราดให้ละเอียด"),
            (-1, "เตรียมเมล็ด", "แช่เมล็ดพันธุ์", f"แช่เมล็ด 24 ชม. หมักในกระสอบ 24 ชม. รวม {seed} กก."),
            (0,  "หว่าน", "หว่านข้าวงอก", f"หว่านเมล็ดงอกอัตรา 15-20 กก./ไร่ รวม {seed} กก."),
            (15, "ระยะแตกกอ", "ใส่ปุ๋ยครั้งที่ 1", f"ปุ๋ยสูตร 16-20-0 อัตรา 25 กก./ไร่ รวม {f1} กก. (ถามผู้ช่วย AI สำหรับคำแนะนำเฉพาะพันธุ์)"),
            (round(h * 0.5), "ระยะกำเนิดช่อดอก", "ใส่ปุ๋ยครั้งที่ 2", f"ปุ๋ยสูตร 46-0-0 อัตรา 20 กก./ไร่ รวม {f2} กก."),
            (round(h * 0.8), "ระยะออกรวง", "ตรวจสอบรวงข้าว", "สังเกตการออกรวง ตรวจโรคและแมลงศัตรูข้าว"),
            (h, "เก็บเกี่ยว", "เก็บเกี่ยวผลผลิต", "เก็บเกี่ยวเมื่อเมล็ดสุก 80% ของรวง"),
        ]

    # throw (นาโยน)
    trays = round(30 * area_rai)
    seed = round(6 * area_rai, 1)
    return [
        (-15, "เตรียมกล้า", "เพาะกล้าในถาด", f"เพาะกล้าในถาด 434 หลุม จำนวน {trays} ถาด เมล็ด {seed} กก."),
        (-7,  "เตรียมดิน", "ไถและคราดแปลงนา", "ไถดินลึก 15-20 ซม. คราดให้ละเอียด ปรับระดับน้ำ"),
        (0,   "โยนกล้า", "โยนต้นกล้าลงแปลง", "โยนกล้าอายุ 15 วัน กระจายให้ทั่วแปลง ประมาณ 30 ถาด/ไร่"),
        (20,  "ระยะแตกกอ", "ใส่ปุ๋ยครั้งที่ 1", f"ปุ๋ยสูตร 16-20-0 อัตรา 25 กก./ไร่ รวม {f1} กก. (ถามผู้ช่วย AI สำหรับคำแนะนำเฉพาะพันธุ์)"),
        (round(harvest_age_days * 0.5), "ระยะกำเนิดช่อดอก", "ใส่ปุ๋ยครั้งที่ 2", f"ปุ๋ยสูตร 46-0-0 อัตรา 20 กก./ไร่ รวม {f2} กก."),
        (round(harvest_age_days * 0.8), "ระยะออกรวง", "ตรวจสอบรวงข้าว", "สังเกตการออกรวง ตรวจโรคและแมลงศัตรูข้าว"),
        (harvest_age_days, "เก็บเกี่ยว", "เก็บเกี่ยวผลผลิต", "เก็บเกี่ยวเมื่อเมล็ดสุก 80% ของรวง"),
    ]


def _calculate_resources(planting_method: str, area_rai: float) -> dict:
    if planting_method == "broadcast":
        seed = round(17 * area_rai, 1)
        trays = None
    elif planting_method == "throw":
        seed = round(6 * area_rai, 1)
        trays = round(30 * area_rai)
    else:
        seed = round(5 * area_rai, 1)
        trays = None
    return {
        "seed_kg": seed,
        "fertilizer1_kg": round(25 * area_rai, 1),
        "fertilizer2_kg": round(20 * area_rai, 1),
        "seedling_trays": trays,
    }


class PlanService:
    def generate_plan(
        self,
        variety_name: str,
        harvest_age_days: int,
        planting_method: str,
        start_date: date,
        area_rai: float,
    ) -> tuple[list[dict], dict]:
        raw_tasks = _build_tasks(planting_method, harvest_age_days, area_rai)
        tasks = [
            {
                "day": day,
                "stage": stage,
                "task_name": task_name,
                "description": desc,
                "date": start_date + timedelta(days=day),
            }
            for day, stage, task_name, desc in raw_tasks
        ]
        resources = _calculate_resources(planting_method, area_rai)
        return tasks, resources


plan_service = PlanService()
