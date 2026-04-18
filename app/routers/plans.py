from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm.session import Session

from app.dependencies import get_current_user, get_db
from app.models.plan import PlanTask, PlantingPlan
from app.models.variety import RiceVariety
from app.schemas.plan import PlanCloneRequest, PlanRequest, PlanResources, PlanResponse, PlanTaskResponse, PlanUpdateRequest
from app.services.plan_service import PLANTING_DAY, calculate_resources, plan_service

router = APIRouter(prefix="/plans", tags=["plans"])


def _task_to_response(t: PlanTask) -> PlanTaskResponse:
    return PlanTaskResponse(
        id=str(t.id),
        day=int(t.day),
        stage=str(t.stage),
        task_name=str(t.task_name),
        description=str(t.description) if t.description else None,
        date=str(t.date),
        is_completed=bool(t.is_completed),
    )


def _plan_to_response(plan: PlantingPlan, tasks: list, resources: dict, actual_planting_date, is_photoperiod_sensitive: bool = False) -> PlanResponse:
    return PlanResponse(
        id=str(plan.id),
        variety_id=str(plan.variety_id),
        variety_name=str(plan.variety_name),
        start_date=str(plan.start_date),
        actual_planting_date=str(actual_planting_date),
        area_rai=float(plan.area_rai),
        plot_name=str(plan.plot_name) if plan.plot_name else None,
        planting_method=str(plan.planting_method),
        soil_type=str(plan.soil_type) if plan.soil_type else "clay",
        is_photoperiod_sensitive=is_photoperiod_sensitive,
        resources=PlanResources(**resources),
        tasks=[_task_to_response(t) for t in tasks],
        created_at=str(plan.created_at),
    )


def _resolve_fert(variety: RiceVariety) -> tuple[float, float, str, str, str, str]:
    """Returns (fert1_rate, fert2_rate, fert1_formula, fert2_formula, fert1_note, fert2_note)"""
    fert1_rate = float(variety.fert1_rate)
    fert2_rate = float(variety.fert2_rate)
    fert1_formula = str(variety.fert1_formula)
    fert2_formula = str(variety.fert2_formula)
    fert1_note = str(variety.fert1_note) if variety.fert1_note else ""
    fert2_note = str(variety.fert2_note) if variety.fert2_note else ""
    return fert1_rate, fert2_rate, fert1_formula, fert2_formula, fert1_note, fert2_note


@router.post("/", response_model=PlanResponse)
def create_plan(
    body: PlanRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    variety = db.query(RiceVariety).filter(RiceVariety.id == body.variety_id, RiceVariety.is_active == True).first()
    if not variety:
        raise HTTPException(status_code=404, detail="ไม่พบพันธุ์ข้าว")

    if body.planting_method not in variety.supported_methods:
        raise HTTPException(
            status_code=400,
            detail=f"พันธุ์ {variety.name} ไม่รองรับวิธีปลูก '{body.planting_method}'"
        )

    fert1_rate, fert2_rate, fert1_formula, fert2_formula, fert1_note, fert2_note = _resolve_fert(variety)

    try:
        tasks, resources, actual_planting_date = plan_service.generate_plan(
            planting_method=body.planting_method,
            start_date=body.start_date,
            area_rai=body.area_rai,
            soil_type=body.soil_type,
            tillering_day=int(variety.tillering_day) if variety.tillering_day is not None else None,
            panicle_initiation_day=int(variety.panicle_initiation_day) if variety.panicle_initiation_day is not None else None,
            heading_day=int(variety.heading_day) if variety.heading_day is not None else None,
            fert1_rate=fert1_rate,
            fert2_rate=fert2_rate,
            fert1_formula=fert1_formula,
            fert2_formula=fert2_formula,
            fert1_note=fert1_note,
            fert2_note=fert2_note,
            is_photoperiod_sensitive=bool(variety.is_photoperiod_sensitive),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    plan = PlantingPlan(
        user_id=current_user.id,
        variety_id=body.variety_id,
        variety_name=str(variety.name),
        start_date=body.start_date,
        area_rai=body.area_rai,
        plot_name=body.plot_name,
        planting_method=body.planting_method,
        soil_type=body.soil_type,
        resources_snapshot=resources,
    )
    db.add(plan)
    db.flush()

    for t in tasks:
        db.add(PlanTask(
            plan_id=plan.id,
            day=t["day"],
            stage=t["stage"],
            task_name=t["task_name"],
            description=t["description"],
            date=t["date"],
        ))

    db.commit()
    db.refresh(plan)

    plan_tasks = db.query(PlanTask).filter(PlanTask.plan_id == plan.id).order_by(PlanTask.day).all()
    return _plan_to_response(plan, plan_tasks, resources, actual_planting_date, bool(variety.is_photoperiod_sensitive))


@router.get("/", response_model=list[PlanResponse])
def get_plans(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    plans = db.query(PlantingPlan).filter(PlantingPlan.user_id == current_user.id).all()
    result = []
    for p in plans:
        tasks = db.query(PlanTask).filter(PlanTask.plan_id == p.id).order_by(PlanTask.day).all()
        variety = db.query(RiceVariety).filter(RiceVariety.id == p.variety_id).first()
        resources = p.resources_snapshot
        if not resources:
            if variety:
                fert1_rate, fert2_rate, fert1_formula, _f2f, _f1n, _f2n = _resolve_fert(variety)
                resources = calculate_resources(
                    planting_method=str(p.planting_method),
                    area_rai=float(p.area_rai),
                    soil_type=str(p.soil_type) if p.soil_type else "clay",
                    fert1_rate=fert1_rate,
                    fert2_rate=fert2_rate,
                    fert1_formula=fert1_formula,
                )
                p.resources_snapshot = resources
                db.commit()
            else:
                resources = {"seed_kg": 0.0, "fertilizer1_kg": 0.0, "fertilizer1_formula": "", "fertilizer2_kg": 0.0, "fertilizer2_formula": ""}
        p_offset = PLANTING_DAY.get(str(p.planting_method), 0)
        actual_planting_date = p.start_date + timedelta(days=p_offset)
        result.append(_plan_to_response(p, tasks, resources, actual_planting_date, bool(variety.is_photoperiod_sensitive) if variety else False))
    return result


@router.patch("/{plan_id}/tasks/{task_id}/toggle", response_model=PlanTaskResponse)
def toggle_task(
    plan_id: str,
    task_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    plan = db.query(PlantingPlan).filter(
        PlantingPlan.id == plan_id,
        PlantingPlan.user_id == current_user.id,
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="ไม่พบแผน")

    task = db.query(PlanTask).filter(PlanTask.id == task_id, PlanTask.plan_id == plan_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="ไม่พบงาน")

    task.is_completed = not task.is_completed
    db.commit()
    db.refresh(task)
    return _task_to_response(task)


@router.patch("/{plan_id}", response_model=PlanResponse)
def update_plan(
    plan_id: str,
    body: PlanUpdateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    plan = db.query(PlantingPlan).filter(
        PlantingPlan.id == plan_id,
        PlantingPlan.user_id == current_user.id,
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="ไม่พบแผน")

    if body.plot_name is not None:
        plan.plot_name = body.plot_name
    if body.area_rai is not None:
        if body.area_rai <= 0:
            raise HTTPException(status_code=400, detail="พื้นที่ต้องมากกว่า 0")
        plan.area_rai = body.area_rai
    if body.soil_type is not None:
        if body.soil_type not in ["clay", "loam", "sandy"]:
            raise HTTPException(status_code=400, detail="ประเภทดินไม่ถูกต้อง")
        plan.soil_type = body.soil_type

    # Recalc resources snapshot (ไม่แตะ tasks เพื่อเก็บ progress เดิม)
    # ถ้าเปลี่ยนดิน → ใช้สูตรปุ๋ยตามดินใหม่ (soil wins); ไม่เปลี่ยนดิน → คงสูตรพันธุ์เดิม
    if body.area_rai is not None or body.soil_type is not None:
        variety = db.query(RiceVariety).filter(RiceVariety.id == plan.variety_id).first()
        if not variety:
            raise HTTPException(status_code=404, detail="ไม่พบพันธุ์ข้าวของแผนนี้")
        fert1_rate, fert2_rate, fert1_formula, _f2f, _f1n, _f2n = _resolve_fert(variety)
        formula_override = "" if body.soil_type is not None else fert1_formula
        plan.resources_snapshot = calculate_resources(
            planting_method=str(plan.planting_method),
            area_rai=float(plan.area_rai),
            soil_type=str(plan.soil_type),
            fert1_rate=fert1_rate,
            fert2_rate=fert2_rate,
            fert1_formula=formula_override,
        )

    db.commit()
    db.refresh(plan)

    tasks = db.query(PlanTask).filter(PlanTask.plan_id == plan.id).order_by(PlanTask.day).all()
    variety = db.query(RiceVariety).filter(RiceVariety.id == plan.variety_id).first()
    p_offset = PLANTING_DAY.get(str(plan.planting_method), 0)
    actual_planting_date = plan.start_date + timedelta(days=p_offset)
    return _plan_to_response(
        plan, tasks, plan.resources_snapshot or {}, actual_planting_date,
        bool(variety.is_photoperiod_sensitive) if variety else False,
    )


@router.post("/{plan_id}/clone", response_model=PlanResponse)
def clone_plan(
    plan_id: str,
    body: PlanCloneRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    src = db.query(PlantingPlan).filter(
        PlantingPlan.id == plan_id,
        PlantingPlan.user_id == current_user.id,
    ).first()
    if not src:
        raise HTTPException(status_code=404, detail="ไม่พบแผนต้นฉบับ")

    variety = db.query(RiceVariety).filter(RiceVariety.id == src.variety_id, RiceVariety.is_active == True).first()
    if not variety:
        raise HTTPException(status_code=404, detail="พันธุ์ข้าวของแผนต้นฉบับไม่พร้อมใช้งาน")

    fert1_rate, fert2_rate, fert1_formula, fert2_formula, fert1_note, fert2_note = _resolve_fert(variety)

    try:
        tasks, resources, actual_planting_date = plan_service.generate_plan(
            planting_method=str(src.planting_method),
            start_date=body.start_date,
            area_rai=float(src.area_rai),
            soil_type=str(src.soil_type) if src.soil_type else "clay",
            tillering_day=int(variety.tillering_day) if variety.tillering_day is not None else None,
            panicle_initiation_day=int(variety.panicle_initiation_day) if variety.panicle_initiation_day is not None else None,
            heading_day=int(variety.heading_day) if variety.heading_day is not None else None,
            fert1_rate=fert1_rate,
            fert2_rate=fert2_rate,
            fert1_formula=fert1_formula,
            fert2_formula=fert2_formula,
            fert1_note=fert1_note,
            fert2_note=fert2_note,
            is_photoperiod_sensitive=bool(variety.is_photoperiod_sensitive),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    new_plan = PlantingPlan(
        user_id=current_user.id,
        variety_id=src.variety_id,
        variety_name=str(src.variety_name),
        start_date=body.start_date,
        area_rai=float(src.area_rai),
        plot_name=body.plot_name if body.plot_name is not None else (f"{src.plot_name} (สำเนา)" if src.plot_name else None),
        planting_method=str(src.planting_method),
        soil_type=str(src.soil_type) if src.soil_type else "clay",
        resources_snapshot=resources,
    )
    db.add(new_plan)
    db.flush()

    for t in tasks:
        db.add(PlanTask(
            plan_id=new_plan.id,
            day=t["day"],
            stage=t["stage"],
            task_name=t["task_name"],
            description=t["description"],
            date=t["date"],
        ))

    db.commit()
    db.refresh(new_plan)

    new_tasks = db.query(PlanTask).filter(PlanTask.plan_id == new_plan.id).order_by(PlanTask.day).all()
    return _plan_to_response(new_plan, new_tasks, resources, actual_planting_date, bool(variety.is_photoperiod_sensitive))


@router.delete("/{plan_id}", status_code=204)
def delete_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    plan = db.query(PlantingPlan).filter(
        PlantingPlan.id == plan_id,
        PlantingPlan.user_id == current_user.id,
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="ไม่พบแผน")

    db.query(PlanTask).filter(PlanTask.plan_id == plan_id).delete()
    db.delete(plan)
    db.commit()
