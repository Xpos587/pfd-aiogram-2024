from typing import Optional

from ..models import DBFeedback
from .base import BaseRepository


class FeedbackRepository(BaseRepository[DBFeedback]):
    _entity = DBFeedback

    async def create_feedback(
        self,
        user: int,  # Изменено с DBUser на int
        question: str,
        answer: str,
        checklist: Optional[str] = None,  # Добавлен параметр checklist
    ) -> DBFeedback:
        """Create new feedback entry."""
        feedback = DBFeedback(
            user=user,  # Изменено с user_id на user
            question=question,
            answer=answer,
            checklist=checklist,  # Добавлено поле checklist
        )
        await self.commit(feedback)
        return feedback

    async def set_rating(
        self,
        feedback_id: int,
        rating: bool,
    ) -> Optional[DBFeedback]:
        """Update feedback rating."""
        feedback = await self.get(id=feedback_id)
        if feedback:
            feedback.is_helpful = rating  # Изменено с rating на is_helpful
            await self.commit(feedback)
        return feedback
