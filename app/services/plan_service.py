from datetime import date, timedelta

SOIL_FERT1_FORMULA: dict[str, str] = {
    "clay":  "16-20-0",
    "loam":  "16-16-8",
    "sandy": "16-16-8",
}

# วันปลูกจริงตามวิธีปลูก (offset จาก Day 0 = start_date)
PLANTING_DAY: dict[str, int] = {
    "transplant": 21,   # ตากดิน 14 วัน + อายุกล้า 21 วัน
    "broadcast":  10,   # ตากดิน 7 วัน + เตรียมเมล็ดงอก 3 วัน
    "throw":      15,   # กล้าถาดอายุ 15 วัน
}


def _build_tasks(
    planting_method: str,
    area_rai: float,
    # ทุก day ด้านล่างเป็น absolute offset จาก start_date (Day 0) แล้ว
    fert1_day: int,
    fert2_day: int,
    heading_day: int,
    drain_day: int,
    harvest_day: int,
    soil_type: str,
    fert1_rate: float,
    fert2_rate: float,
    fert1_formula: str = "",
    fert1_note: str = "",
    fert2_note: str = "",
) -> list[tuple]:
    resolved_f1 = fert1_formula or SOIL_FERT1_FORMULA.get(soil_type, "16-20-0")
    resolved_f2 = "46-0-0"

    f1 = round(fert1_rate * area_rai, 1)
    f2 = round(fert2_rate * area_rai, 1)
    fert1_desc = f"ปุ๋ยสูตร {resolved_f1} อัตรา {fert1_rate} กก./ไร่ รวม {f1} กก." + (f" — {fert1_note}" if fert1_note else "")
    fert2_desc = f"ปุ๋ยสูตร {resolved_f2} อัตรา {fert2_rate} กก./ไร่ รวม {f2} กก." + (f" — {fert2_note}" if fert2_note else "")

    p        = PLANTING_DAY[planting_method]   # Day ที่ลงแปลง (absolute จาก Day 0)
    mid_prep = 7                               # ไถแปรวันที่ 7 เสมอ (ตากดินอย่างน้อย 7 วัน)
    water_day = p - 3                          # 3 วันก่อนลงแปลง

    # --- งานเตรียมดิน (Day 0 = start_date) ---
    prep_tasks: list[tuple] = [
        (0,        "เตรียมดิน", "ไถดะ",  "ไถพลิกดินครั้งแรก ตากดินไว้ 7-14 วัน เพื่อกำจัดวัชพืชและระบายสารพิษ"),
        (mid_prep, "เตรียมดิน", "ไถแปร", "ไถครั้งที่สอง ย่อยดินและคลุกเคล้าฟางให้สลายตัว"),
    ]

    # --- งาน 3 วันก่อนลงแปลง (แตกต่างตามวิธีปลูก) ---
    if planting_method == "broadcast":
        water_prep_tasks = [
            (water_day, "เตรียมดิน", "ทำเทือก",              "ปรับระดับดินให้เรียบกริบ เพื่อให้น้ำท่วมสม่ำเสมอทั้งแปลง"),
            (water_day, "จัดการน้ำ", "เตรียมดินสำหรับหว่าน", "ระบายน้ำออกให้ดินแฉะพอดี (ไม่ให้มีน้ำขัง) เพื่อเตรียมหว่านเมล็ดงอก"),
        ]
    elif planting_method == "transplant":
        water_prep_tasks = [
            (water_day, "เตรียมดิน", "ทำเทือก",      "คราดดินให้ละเอียดเป็นเทือก ปรับระดับให้สม่ำเสมอ"),
            (water_day, "จัดการน้ำ", "ขังน้ำรอปักดำ", "ปล่อยน้ำเข้าแปลง ขังระดับ 5-10 ซม. เตรียมพร้อมรับต้นกล้า"),
        ]
    else:  # throw
        water_prep_tasks = [
            (water_day, "เตรียมดิน", "ทำเทือก",    "คราดดินให้ละเอียด ปรับระดับดินให้สม่ำเสมอ"),
            (water_day, "จัดการน้ำ", "ลดระดับน้ำ", "ลดระดับน้ำให้เหลือคลุมผิวดินเล็กน้อย เพื่อให้ต้นกล้าที่โยนลงยึดดินได้"),
        ]

    # --- งานเพาะกล้า/เตรียมเมล็ด (Day 0) + งานลงแปลง (Day p) ---
    if planting_method == "transplant":
        method_tasks = [
            (0, "เตรียมกล้า", "เพาะกล้า",     "แช่เมล็ดพันธุ์ 24 ชม. หุ้มเมล็ด 30-48 ชม. เพาะในแปลงกล้า อัตรา 5-7 กก./ไร่"),
            (p, "ปักดำ",      "ปักดำต้นกล้า", "ปักดำต้นกล้าอายุ 21 วัน ระยะ 20×20 ซม. 3-5 ต้นต่อกอ"),
        ]
    elif planting_method == "broadcast":
        seed = round(17.0 * area_rai, 1)
        method_tasks = [
            (0, "เตรียมเมล็ด", "แช่เมล็ดพันธุ์", f"แช่เมล็ด 24 ชม. หุ้มในกระสอบ 30-48 ชม. ให้งอกขนาดตุ่มตา รวม {seed} กก."),
            (p, "หว่าน",       "หว่านข้าวงอก",   f"หว่านเมล็ดงอกอัตรา 15-20 กก./ไร่ รวม {seed} กก. ควรหว่านตอนบ่ายหรือเย็น"),
        ]
    else:  # throw
        trays = round(50 * area_rai)
        seed  = round(6.0 * area_rai, 1)
        method_tasks = [
            (0, "เตรียมกล้า", "เพาะกล้าในถาด",    f"เพาะกล้าในถาดพลาสติกขนาด 561 หลุม จำนวน {trays} ถาด เมล็ด {seed} กก. รดน้ำทุกวัน"),
            (p, "โยนกล้า",    "โยนต้นกล้าลงแปลง", "โยนกล้าอายุ 15 วัน ประมาณ 50 ถาด/ไร่ ลดน้ำให้เหลือคลุมผิวดินก่อนโยน"),
        ]

    # --- งานหลังปลูก (ใช้ absolute day ที่ generate_plan คำนวณมาแล้ว) ---
    post_tasks = [
        (fert1_day,       "ระยะแตกกอ",        "ใส่ปุ๋ยครั้งที่ 1",       fert1_desc),
        (fert2_day,       "ระยะกำเนิดช่อดอก", "ใส่ปุ๋ยครั้งที่ 2",       fert2_desc),
        (heading_day - 7, "จัดการน้ำ",         "รักษาระดับน้ำช่วงวิกฤต", "เพิ่มระดับน้ำให้สูง 5-10 ซม. เพื่อรองรับการสร้างรวง ห้ามขาดน้ำเด็ดขาดในช่วงนี้"),
        (heading_day,     "ระยะออกรวง",        "ตรวจสอบรวงข้าว",          "ระยะออกรวง: สังเกตการออกดอกและรักษาระดับน้ำให้คงที่เพื่อการสร้างเมล็ดที่สมบูรณ์"),
        (drain_day,       "จัดการน้ำ",         "ระบายน้ำออก",             "ระบายน้ำออกจากแปลง ทำก่อนเก็บเกี่ยว 12 วัน เพื่อเร่งการสุกแก่และให้ดินแห้งรับรถเกี่ยว"),
        (harvest_day,     "เก็บเกี่ยว",        "เก็บเกี่ยวผลผลิต",        "เก็บเกี่ยวเมื่อเมล็ดสุก 80% ของรวง"),
    ]

    all_tasks = prep_tasks + water_prep_tasks + method_tasks + post_tasks
    all_tasks.sort(key=lambda x: x[0])
    return all_tasks


def _calculate_resources(
    planting_method: str,
    area_rai: float,
    soil_type: str,
    fert1_rate: float,
    fert2_rate: float,
    fert1_formula: str = "",
) -> dict:
    resolved_f1 = fert1_formula or SOIL_FERT1_FORMULA.get(soil_type, "16-20-0")

    if planting_method == "broadcast":
        seed  = round(17.0 * area_rai, 1)
        trays = None
    elif planting_method == "throw":
        seed  = round(6.0 * area_rai, 1)
        trays = round(50 * area_rai)
    else:  # transplant
        seed  = round(5.0 * area_rai, 1)
        trays = None

    return {
        "seed_kg": seed,
        "fertilizer1_kg": round(fert1_rate * area_rai, 1),
        "fertilizer1_formula": resolved_f1,
        "fertilizer2_kg": round(fert2_rate * area_rai, 1),
        "fertilizer2_formula": "46-0-0",
        "seedling_trays": trays,
    }


class PlanService:
    def generate_plan(
        self,
        harvest_age_days: int,
        planting_method: str,
        start_date: date,
        area_rai: float,
        soil_type: str,
        tillering_day: int | None,
        panicle_initiation_day: int | None,
        heading_day: int | None,
        fert1_rate: float,
        fert2_rate: float,
        fert1_formula: str = "",
        fert1_note: str = "",
        fert2_note: str = "",
        heading_calendar_date: date | None = None,   # วันออกดอกตามปฏิทิน (ข้าวไวแสง) เช่น date(2026, 11, 20)
    ) -> tuple[list[dict], dict, date]:
        p = PLANTING_DAY[planting_method]          # offset จาก Day 0 ถึงวันลงแปลง
        actual_planting_date = start_date + timedelta(days=p)

        # --- Resolve growth stage offsets (นับจากวันลงแปลง) ---
        if heading_calendar_date is not None:
            # ข้าวไวแสง: heading วันที่แน่นอนตามปฏิทิน
            # แปลงเป็น offset จากวันลงแปลง = (calendar_date - start_date).days - p
            heading_abs = (heading_calendar_date - start_date).days
            g_heading   = heading_abs - p
            g_panicle   = panicle_initiation_day if panicle_initiation_day is not None else g_heading - 30
            g_harvest   = g_heading + 30          # เก็บเกี่ยวหลังออกดอก 30 วัน
        else:
            # ข้าวไม่ไวแสง: คำนวณจาก harvest_age_days
            g_harvest   = harvest_age_days
            g_heading   = heading_day            if heading_day            is not None else harvest_age_days - 30
            g_panicle   = panicle_initiation_day if panicle_initiation_day is not None else harvest_age_days - 60

        g_tillering = tillering_day if tillering_day is not None else round(g_harvest * 0.25)

        # แปลงเป็น absolute day จาก start_date (Day 0) — บวก p ที่เดียว ไม่ซ้ำ
        fert1_day_abs  = p + g_tillering
        fert2_day_abs  = p + g_panicle
        heading_abs    = p + g_heading
        harvest_abs    = heading_abs + 30    # บังคับ 30 วันหลังออกรวงเสมอ
        drain_abs      = harvest_abs - 12    # ระบายน้ำ 12 วันก่อนเก็บเกี่ยว (= 18 วันหลังออกรวง)

        raw_tasks = _build_tasks(
            planting_method, area_rai,
            fert1_day_abs, fert2_day_abs, heading_abs, drain_abs, harvest_abs,
            soil_type, fert1_rate, fert2_rate, fert1_formula, fert1_note, fert2_note,
        )

        # Re-base: งานแรกต้อง Day 0 เสมอ (safety net)
        if raw_tasks:
            min_day = min(t[0] for t in raw_tasks)
            if min_day != 0:
                raw_tasks = [(day - min_day, stage, name, desc) for day, stage, name, desc in raw_tasks]
                actual_planting_date = start_date + timedelta(days=p - min_day)

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
        resources = _calculate_resources(
            planting_method, area_rai, soil_type,
            fert1_rate, fert2_rate, fert1_formula,
        )
        return tasks, resources, actual_planting_date


plan_service = PlanService()
