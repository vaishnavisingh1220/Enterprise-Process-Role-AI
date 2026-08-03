from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ai.client import get_llm_client
from database.session import get_db
from services import chat_service
from api.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/ask", response_model=ChatResponse)
def ask(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Free-text question answering, grounded in the same reasoning engine
    every other endpoint uses. The question is routed to an intent and
    matched entities in plain Python (services/query_router.py) BEFORE
    the LLM ever sees it — the LLM only narrates the evidence that
    routing step assembled. Questions outside the dataset's scope get an
    explicit "here's what I actually cover" answer instead of a guess.
    """
    llm_client = get_llm_client()
    return chat_service.answer_question(db, llm_client, request.message)