from datetime import date

from app.services.rag_service import rag_service


class PlanService:
    def generate_plan(self, variety_name: str, start_date: date, area_rai: float) -> dict:
        query = (
            f"สร้างแผนการปลูกข้าวพันธุ์ {variety_name} "
            f"เริ่มปลูกวันที่ {start_date} พื้นที่ {area_rai} ไร่ "
            f"ระบุขั้นตอน ระยะเวลา และการดูแลแต่ละช่วง"
        )
        return rag_service.ask_question(query)


plan_service = PlanService()
