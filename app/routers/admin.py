from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm.session import Session

from app.dependencies import get_db, require_admin
from app.models.chat import ChatHistory

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/faq")
def get_faq(db: Session = Depends(get_db), _=Depends(require_admin)):
    results = (
        db.query(ChatHistory.question, func.count(ChatHistory.question).label("count"))
        .group_by(ChatHistory.question)
        .order_by(func.count(ChatHistory.question).desc())
        .limit(10)
        .all()
    )
    return [{"question": row.question, "count": row.count} for row in results]
