from datetime import date, timedelta

SOIL_FERT1_FORMULA: dict[str, str] = {
    "clay": "16-20-0",
    "loam": "16-16-8",
    "sandy": "16-16-8",
}

# ดินทรายชะล้างปุ๋ยง่าย → ใส่เพิ่ม, ดินเหนียวอุ้มธาตุอาหารดี → มาตรฐาน
SOIL_FERT_MULTIPLIER: dict[str, float] = {
    "clay": 1.0,
    "loam": 1.1,
    "sandy": 1.2,
}

# วันปลูกจริงตามวิธีปลูก (offset จาก Day 0 = start_date)
# broadcast: ทำเทือก Day 7 + หว่าน Day 10
# throw:     ทำเทือก Day 12 + โยน Day 15 (กล้าถาด 15 วัน)
# transplant:ทำเทือก Day 12 + ขังน้ำ Day 13-24 + ปักดำ Day 25 (กล้าอายุ 25 วัน)
PLANTING_DAY: dict[str, int] = {
    "transplant": 25,
    "broadcast": 10,
    "throw": 15,
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
    fert2_formula: str = "",
    fert1_note: str = "",
    fert2_note: str = "",
) -> list[tuple]:
    resolved_f1 = fert1_formula or SOIL_FERT1_FORMULA.get(soil_type, "16-20-0")
    resolved_f2 = fert2_formula or "46-0-0"
    multiplier = SOIL_FERT_MULTIPLIER.get(soil_type, 1.0)

    adj_f1_rate = round(fert1_rate * multiplier, 1)
    adj_f2_rate = round(fert2_rate * multiplier, 1)
    f1 = round(adj_f1_rate * area_rai, 1)
    f2 = round(adj_f2_rate * area_rai, 1)
    fert1_desc = f"ปุ๋ยสูตร {resolved_f1} อัตรา {adj_f1_rate} กก./ไร่ รวม {f1} กก." + (
        f" — {fert1_note}" if fert1_note else ""
    )
    fert2_desc = f"ปุ๋ยสูตร {resolved_f2} อัตรา {adj_f2_rate} กก./ไร่ รวม {f2} กก." + (
        f" — {fert2_note}" if fert2_note else ""
    )

    p = PLANTING_DAY[planting_method]  # Day ที่ลงแปลง (absolute จาก Day 0)

    # ===== เตรียมดิน (7-5-3 Logic) =====
    # Day 0: ไถดะ → Day 7: ไถแปร → Day 12: ทำเทือก (ยกเว้น broadcast ทำเทือก Day 7)
    tasks: list[tuple] = [
        (
            0,
            "เตรียมดิน",
            "ไถดะ",
            "ไถพลิกดินครั้งแรก ตากดินไว้ 7 วัน เพื่อกำจัดวัชพืช เชื้อโรค และระบายก๊าซพิษออกจากดิน",
        ),
        (
            7,
            "เตรียมดิน",
            "ไถแปร",
            "ไถย่อยดินครั้งที่สอง คลุกเคล้าฟางข้าวและอินทรียวัตถุให้สลายตัว เตรียมพื้นดินสำหรับทำเทือก",
        ),
    ]

    # ===== ทำเทือก + เตรียมก่อนปลูก =====
    if planting_method == "broadcast":
        # ทำเทือก Day 7 (เดียวกับไถแปร) เพื่อให้หว่านทัน Day 10
        tasks += [
            (
                7,
                "เตรียมดิน",
                "ทำเทือก",
                "ปั่นดินให้ละเอียดเป็นเลน ปรับระดับดินให้เรียบสม่ำเสมอ เพื่อให้น้ำท่วมถึงทุกพื้นที่และเมล็ดงอกกระจายทั่วแปลง",
            ),
            (
                7,
                "จัดการน้ำ",
                "เตรียมดินสำหรับหว่าน",
                "ระบายน้ำออกให้ดินแฉะพอดี (ไม่ขังน้ำ) เพื่อให้เมล็ดงอกยึดติดดินได้หลังหว่าน",
            ),
        ]
    else:
        # throw และ transplant: ทำเทือก Day 12
        tasks.append(
            (
                12,
                "เตรียมดิน",
                "ทำเทือก",
                "ปั่นดินให้ละเอียดเป็นเลน ปรับระดับดินให้สม่ำเสมอ ช่วยลดการสูญเสียน้ำและควบคุมวัชพืชในแปลง",
            )
        )
        if planting_method == "transplant":
            # Day 13-24: ขังน้ำตื้นรอกล้า (คุมวัชพืช + รอกล้าครบ 25 วัน)
            tasks.append(
                (
                    13,
                    "จัดการน้ำ",
                    "ขังน้ำตื้นรอกล้า",
                    "ปล่อยน้ำเข้าแปลง ขังระดับ 3-5 ซม. ตั้งแต่วันที่ 13 จนถึงวันปักดำ (วันที่ 24) เพื่อควบคุมวัชพืชและเตรียมดินรับต้นกล้า",
                )
            )
        else:  # throw
            tasks.append(
                (
                    12,
                    "จัดการน้ำ",
                    "ลดระดับน้ำก่อนโยนกล้า",
                    "ลดระดับน้ำให้เหลือคลุมผิวดินเล็กน้อย (1-2 ซม.) เพื่อให้รากกล้าที่โยนลงยึดดินได้ก่อนเพิ่มระดับน้ำ",
                )
            )

    # ===== เพาะกล้า/เตรียมเมล็ด (Day 0) + งานรายวันดูแลกล้า (Day 1) + ลงแปลง (Day p) =====
    if planting_method == "transplant":
        tasks += [
            (
                0,
                "เตรียมกล้า",
                "เพาะกล้า",
                "แช่เมล็ดพันธุ์ 24 ชม. หุ้มเมล็ดในกระสอบ 30-48 ชม. จนงอกขนาดตุ่มตา แล้วหว่านในแปลงกล้า อัตรา 5-7 กก./ไร่",
            ),
            (
                1,
                "ดูแลกล้า",
                "ดูแลแปลงกล้า (รายวัน)",
                "รดน้ำเช้า-เย็นทุกวัน และตรวจเช็คความแข็งแรงของต้นกล้าจนกว่าจะถึงวันปักดำ",
            ),
            (
                p,
                "ปักดำ",
                "ปักดำต้นกล้า",
                "ปักดำต้นกล้าอายุ 25 วัน ระยะ 20×20 ซม. 3-5 ต้นต่อกอ ให้รากจมดินประมาณ 2-3 ซม.",
            ),
        ]
    elif planting_method == "broadcast":
        seed = round(17.0 * area_rai, 1)
        tasks += [
            (
                0,
                "เตรียมเมล็ด",
                "แช่เมล็ดพันธุ์",
                f"แช่เมล็ด 24 ชม. หุ้มในกระสอบ 30-48 ชม. ให้งอกขนาดตุ่มตา รวม {seed} กก.",
            ),
            (
                p,
                "หว่าน",
                "หว่านข้าวงอก",
                f"หว่านเมล็ดงอกอัตรา 15-20 กก./ไร่ รวม {seed} กก. ควรหว่านตอนบ่ายหรือเย็นเพื่อลดความเสียหายจากแสงแดด",
            ),
        ]
    else:  # throw
        trays = round(50 * area_rai)
        seed = round(6.0 * area_rai, 1)
        tasks += [
            (
                0,
                "เตรียมกล้า",
                "เพาะกล้าในถาด",
                f"เพาะกล้าในถาดพลาสติกขนาด 561 หลุม จำนวน {trays} ถาด เมล็ด {seed} กก. รดน้ำทุกวันจนกล้าแข็งแรง",
            ),
            (
                1,
                "ดูแลกล้า",
                "ดูแลแปลงกล้า (รายวัน)",
                "รดน้ำเช้า-เย็นทุกวัน และตรวจเช็คความแข็งแรงของต้นกล้าจนกว่าจะถึงวันโยนกล้า",
            ),
            (
                p,
                "โยนกล้า",
                "โยนต้นกล้าลงแปลง",
                f"โยนกล้าอายุ 15 วัน จำนวน {trays} ถาด โยนให้กระจายสม่ำเสมอทั่วแปลงที่มีน้ำระดับต่ำ",
            ),
        ]

    # ===== งานหลังปลูก + ระยะสุกแก่ =====
    tasks += [
        (
            p + 7,
            "จัดการน้ำ",
            "จัดการน้ำหลังปลูก",
            "รักษาระดับน้ำ 3-5 ซม. เพื่อควบคุมวัชพืชและช่วยให้ข้าวตั้งตัว ห้ามปล่อยแปลงแห้งใน 2 สัปดาห์แรกหลังปลูก",
        ),
        (fert1_day, "ระยะแตกกอ", "ใส่ปุ๋ยครั้งที่ 1", fert1_desc),
        (fert2_day, "ระยะกำเนิดช่อดอก", "ใส่ปุ๋ยครั้งที่ 2", fert2_desc),
        (
            heading_day,
            "ระยะตั้งท้องและออกรวง",
            "ตรวจสอบรวงข้าว",
            "ระยะออกรวง: สังเกตการออกดอกและรักษาระดับน้ำให้คงที่เพื่อสะสมแป้งและสร้างเมล็ดที่สมบูรณ์",
        ),
        (
            heading_day,
            "จัดการน้ำ",
            "รักษาระดับน้ำเพื่อสะสมแป้ง",
            "ขังน้ำระดับ 5-10 ซม. ตลอด 18 วันหลังออกรวง เพื่อส่งเสริมการสร้างน้ำนมและสะสมแป้งในเมล็ด ห้ามปล่อยแปลงแห้ง",
        ),
        (
            drain_day,
            "จัดการน้ำ",
            "ระบายน้ำออกก่อนเกี่ยว",
            "ระบายน้ำออกจากแปลง 12 วันก่อนเก็บเกี่ยว เพื่อให้เมล็ดสุกสม่ำเสมอ ดินแห้งแข็งพอรับน้ำหนักรถเกี่ยว",
        ),
        (
            harvest_day,
            "เก็บเกี่ยว",
            "เก็บเกี่ยวผลผลิต",
            "เก็บเกี่ยวเมื่อเมล็ดสุก 80% ของรวง ควรเกี่ยวในช่วงเช้าเพื่อลดการร่วงหล่นของเมล็ด",
        ),
    ]

    tasks.sort(key=lambda x: x[0])
    return tasks


def _calculate_resources(
    planting_method: str,
    area_rai: float,
    soil_type: str,
    fert1_rate: float,
    fert2_rate: float,
    fert1_formula: str = "",
) -> dict:
    resolved_f1 = fert1_formula or SOIL_FERT1_FORMULA.get(soil_type, "16-20-0")
    multiplier = SOIL_FERT_MULTIPLIER.get(soil_type, 1.0)

    if planting_method == "broadcast":
        seed = round(17.0 * area_rai, 1)
        trays = None
    elif planting_method == "throw":
        seed = round(6.0 * area_rai, 1)
        trays = round(50 * area_rai)
    else:  # transplant
        seed = round(5.0 * area_rai, 1)
        trays = None

    return {
        "seed_kg": seed,
        "fertilizer1_kg": round(fert1_rate * multiplier * area_rai, 1),
        "fertilizer1_formula": resolved_f1,
        "fertilizer2_kg": round(fert2_rate * multiplier * area_rai, 1),
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
        fert2_formula: str = "",
        fert1_note: str = "",
        fert2_note: str = "",
        is_photoperiod_sensitive: bool = False,
    ) -> tuple[list[dict], dict, date]:
        p = PLANTING_DAY[planting_method]  # offset จาก Day 0 ถึงวันลงแปลง
        actual_planting_date = start_date + timedelta(days=p)

        if is_photoperiod_sensitive and start_date.month not in [7, 8]:
            raise ValueError(
                "ข้าวไวแสงควรเริ่มเตรียมงานในช่วงเดือน ก.ค. – ส.ค. เพื่อให้เก็บเกี่ยวได้ตรงตามฤดูกาลและได้คุณภาพสูงสุด"
            )

        # --- Resolve growth stage offsets (นับจากวันลงแปลง) ---
        g_tillering = tillering_day
        g_panicle = panicle_initiation_day
        g_heading = heading_day

        # แปลงเป็น absolute day จาก start_date (Day 0) — บวก p ที่เดียว ไม่ซ้ำ
        fert1_day_abs = p + g_tillering
        fert2_day_abs = p + g_panicle
        heading_abs = p + g_heading
        harvest_abs = heading_abs + 30  # บังคับ 30 วันหลังออกรวงเสมอ
        drain_abs = harvest_abs - 12  # ระบายน้ำ 12 วันก่อนเก็บเกี่ยว (= 18 วันหลังออกรวง)

        # safety: ป้องกันปุ๋ยสลับลำดับ (กรณีปลูกปลาย ส.ค.)
        if fert1_day_abs >= fert2_day_abs:
            fert1_day_abs = fert2_day_abs - 7

        raw_tasks = _build_tasks(
            planting_method,
            area_rai,
            fert1_day_abs,
            fert2_day_abs,
            heading_abs,
            drain_abs,
            harvest_abs,
            soil_type,
            fert1_rate,
            fert2_rate,
            fert1_formula,
            fert2_formula,
            fert1_note,
            fert2_note,
        )

        # Re-base: งานแรกต้อง Day 0 เสมอ (safety net)
        if raw_tasks:
            min_day = min(t[0] for t in raw_tasks)
            if min_day != 0:
                raw_tasks = [
                    (day - min_day, stage, name, desc)
                    for day, stage, name, desc in raw_tasks
                ]
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
            planting_method,
            area_rai,
            soil_type,
            fert1_rate,
            fert2_rate,
            fert1_formula,
        )
        return tasks, resources, actual_planting_date


plan_service = PlanService()
