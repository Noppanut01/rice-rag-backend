from fastapi import APIRouter, Depends
from sqlalchemy.orm.session import Session

from app.dependencies import get_current_user, get_db, get_optional_user
from app.models.chat import ChatHistory
from app.schemas.chat import ChatHistoryItem, ChatRequest, ChatResponse
from app.services.rag_service import rag_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    question = body.question
    result = rag_service.ask_question(question)

    if current_user is not None:
        chat_record = ChatHistory(
            user_id=current_user.id,
            question=question,
            answer=result["answer"],
            sources=result["sources"],
            model_used=result["model_used"],
            embedding_model=result["embedding_model"],
            retrieval_strategy=result["retrieval_strategy"],
            chunk_size=result["chunk_size"],
            chunks_retrieved=result["chunks_retrieved"],
            response_time_ms=result["response_time_ms"],
            ram_used_mb=result["ram_used_mb"],
        )
        db.add(chat_record)
        db.commit()

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        response_time_ms=result["response_time_ms"],
        ram_used_mb=result["ram_used_mb"],
        model_used=result["model_used"],
        embedding_model=result["embedding_model"],
        retrieval_strategy=result["retrieval_strategy"],
        chunk_size=result["chunk_size"],
        chunks_retrieved=result["chunks_retrieved"],
    )


@router.post("/no-rag", response_model=ChatResponse)
def chat_no_rag(
    body: ChatRequest,
    current_user=Depends(get_optional_user),
):
    result = rag_service.ask_question_no_rag(body.question)
    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        response_time_ms=result["response_time_ms"],
        ram_used_mb=result["ram_used_mb"],
        model_used=result["model_used"],
        embedding_model=result["embedding_model"],
        retrieval_strategy=result["retrieval_strategy"],
        chunk_size=result["chunk_size"],
        chunks_retrieved=result["chunks_retrieved"],
    )


@router.get("/history", response_model=list[ChatHistoryItem])
def history(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    chat_histories = (
        db.query(ChatHistory).filter(ChatHistory.user_id == current_user.id).all()
    )
    return [
        ChatHistoryItem(
            id=str(h.id),
            question=str(h.question),
            answer=str(h.answer),
            model_used=str(h.model_used),
            created_at=str(h.created_at),
        )
        for h in chat_histories
    ]
