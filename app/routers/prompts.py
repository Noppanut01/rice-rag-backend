from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm.session import Session

from app.dependencies import get_db, require_admin
from app.models.prompt import PromptTemplate
from app.schemas.prompt import PromptTemplateRequest, PromptTemplateResponse
from app.services.rag_service import rag_service

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
def generate_suggestions(_=Depends(require_admin)):
    return rag_service.generate_prompt_suggestions()


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: str,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบ template")
    db.delete(template)
    db.commit()
