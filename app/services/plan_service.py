import json
import re
from datetime import date, timedelta

from fastapi import HTTPException

from app.services.rag_service import rag_service


class PlanService:
    def generate_plan(self, variety_name: str, start_date: date, area_rai: float) -> list[dict]:
        raw = rag_service.generate_plan_from_rag(variety_name, start_date, area_rai)

        # ลอง parse JSON ตรงๆ ก่อน แล้วค่อย fallback ไป regex
        data = None
        try:
            data = json.loads(raw.strip())
        except json.JSONDecodeError:
            match = re.search(r'\{[\s\S]*\}', raw)
            if match:
                try:
                    data = json.loads(match.group())
                except json.JSONDecodeError:
                    pass

        if not data or not data.get("tasks"):
            raise HTTPException(
                status_code=500,
                detail=f"LLM ไม่สามารถสร้างแผนได้ กรุณาลองใหม่อีกครั้ง (raw: {raw[:100]})"
            )

        tasks = []
        for t in data["tasks"]:
            tasks.append({
                "day": int(t["day"]),
                "stage": str(t["stage"]),
                "task_name": str(t["task_name"]),
                "description": t.get("description", ""),
                "date": start_date + timedelta(days=int(t["day"])),
            })
        return tasks


plan_service = PlanService()
