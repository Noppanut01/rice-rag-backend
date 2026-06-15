from fastapi import APIRouter, Depends, status
from sqlalchemy.orm.session import Session

from app.dependencies import get_db, require_admin
from app.models.prompt import PromptTemplate
from app.schemas.prompt import PromptTemplateRequest, PromptTemplateResponse
from app.services.rag_service import rag_service
from app.utils.http_errors import not_found

router = APIRouter(prefix="/prompts", tags=["prompts"])


def _template_to_response(t: PromptTemplate) -> PromptTemplateResponse:
    return PromptTemplateResponse(
        id=str(t.id),
        title=str(t.title),
        content=str(t.content),
        created_at=str(t.created_at),
    )


@router.get("/", response_model=list[PromptTemplateResponse])
def list_templates(db: Session = Depends(get_db)):
    return [_template_to_response(t) for t in db.query(PromptTemplate).all()]


@router.post("/", response_model=PromptTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    body: PromptTemplateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    template = PromptTemplate(
        title=body.title,
        content=body.content,
        created_by=current_user.id,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return _template_to_response(template)


@router.post("/generate", response_model=list[dict])
def generate_suggestions(
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    existing = (
        db.query(PromptTemplate.content)
        .order_by(PromptTemplate.created_at.desc())
        .limit(30)
        .all()
    )
    existing_questions = [row[0] for row in existing]
    return rag_service.generate_prompt_suggestions(existing_questions=existing_questions)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: str,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not template:
        raise not_found("ไม่พบ template")
    db.delete(template)
    db.commit()
