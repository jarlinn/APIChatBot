"""Job controller"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from sqlalchemy import select


from src.app.config import settings
from src.app.db.session import get_async_session
from src.app.dependencies.auth import get_current_active_user
from src.app.models.question import Question, QuestionStatus
from src.app.models.user import User
from src.app.services.email_service import email_service
from src.app.utils.html_templates import get_pending_questions_email_html


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/pending-questions", tags=["jobs"])

@router.post("/", response_model=None)
async def create_alert_email(
    # current_user=Depends(get_current_active_user)
):
    emails = []
    async for session in get_async_session():
        query = select(Question).where(Question.status == QuestionStatus.PENDING)
        result = await session.execute(query)
        pending_questions = result.scalars().all()

        now = datetime.now(timezone.utc)
    
        questions = [
            {
                "question_text": q.question_text,
                "created_at": q.created_at,
                "status": q.status,
                "days_pending": (now - q.created_at).days
            }
            for q in pending_questions
        ]

        emails = (await session.execute(select(User.email).where(User.is_active == True))).scalars().all()
        emails = [email.strip() for email in emails]
        email_original = settings.mailtrap_from_email
        emails_validate = [
            email_original.replace("@gmail.com", "+self@gmail.com") 
            if email == email_original 
            else email 
            for email in emails
        ]

        try:
            for email in emails_validate:
                await email_service.send_email(
                    to_email=email,
                    subject="Tienes Preguntas Pendientes por validar - ChatBot UFPS",
                    html_content=get_pending_questions_email_html(questions),
                    text_content="Valida tus preguntas Pronto!"
                )
        except Exception as e:
            logger.warning(f"Could not send notification: {e}")
            raise HTTPException(status_code=500, detail="Failed to send notifications")
    return {"msg": "job run successfully", "sent_to": len(emails)}
