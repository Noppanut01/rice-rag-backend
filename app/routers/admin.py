from fastapi import APIRouter, Depends
from sqlalchemy import func, or_
from sqlalchemy.orm.session import Session

from app.dependencies import get_db, require_admin
from app.models.chat import ChatHistory
from app.models.user import User
from app.schemas.admin import FaqItem, GapItem
from app.schemas.auth import UserResponse, UserRoleUpdateRequest
from app.utils.http_errors import bad_request, not_found
from app.utils.text import normalize_question

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/faq", response_model=list[FaqItem])
def get_faq(db: Session = Depends(get_db), _=Depends(require_admin)):
    results = (
        db.query(ChatHistory.question, func.count(ChatHistory.question).label("count"))
        .group_by(ChatHistory.question)
        .order_by(func.count(ChatHistory.question).desc())
        .all()
    )

    grouped: dict[str, dict] = {}
    for row in results:
        key = normalize_question(row.question)
        item = grouped.setdefault(
            key,
            {"question": row.question, "count": 0},
        )
        item["count"] += row.count

    normalized_results = sorted(
        grouped.values(),
        key=lambda item: item["count"],
        reverse=True,
    )
    return [
        {"question": row["question"], "count": row["count"]}
        for row in normalized_results[:10]
    ]


@router.get("/gaps", response_model=list[GapItem])
def get_knowledge_gaps(db: Session = Depends(get_db), _=Depends(require_admin)):
    results = (
        db.query(
            ChatHistory.question,
            func.count(ChatHistory.id).label("count"),
            func.max(ChatHistory.created_at).label("last_asked_at"),
        )
        .filter(
            or_(
                ChatHistory.chunks_retrieved == 0,
                ChatHistory.answer.ilike("%ไม่ทราบ%"),
                ChatHistory.answer.ilike("%ไม่พบในเอกสารอ้างอิง%"),
                ChatHistory.answer.ilike("%คำตอบนี้ใช้ความรู้ทั่วไป%"),
            )
        )
        .group_by(ChatHistory.question)
        .order_by(func.count(ChatHistory.id).desc())
        .all()
    )

    grouped: dict[str, dict] = {}
    for row in results:
        key = normalize_question(row.question)
        item = grouped.setdefault(
            key,
            {"question": row.question, "count": 0, "last_asked_at": row.last_asked_at},
        )
        item["count"] += row.count
        if row.last_asked_at and (
            item["last_asked_at"] is None or row.last_asked_at > item["last_asked_at"]
        ):
            item["last_asked_at"] = row.last_asked_at

    normalized_results = sorted(
        grouped.values(),
        key=lambda item: item["count"],
        reverse=True,
    )
    return [
        {
            "question": row["question"],
            "count": row["count"],
            "last_asked_at": row["last_asked_at"].isoformat() if row["last_asked_at"] else None,
        }
        for row in normalized_results[:20]
    ]


@router.get("/users", response_model=list[UserResponse])
def get_all_users(db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.put("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: str,
    req: UserRoleUpdateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    if req.role not in ["admin", "user"]:
        raise bad_request("Invalid role")

    if user_id == current_admin.id:
        raise bad_request("คุณไม่สามารถเปลี่ยนสิทธิ์หรือลดสิทธิ์ตัวเองได้")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise not_found("ไม่พบผู้ใช้งานนี้")
        
    user.role = req.role
    db.commit()
    db.refresh(user)
    return user
