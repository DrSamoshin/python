import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import String, DateTime, ForeignKey, Text, func, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.user import Base


class GoalStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid()
    )
    chat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[GoalStatus] = mapped_column(
        SQLEnum(GoalStatus, name="goal_status"),
        nullable=False
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("goals.id", ondelete="CASCADE"),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    chat: Mapped["Chat"] = relationship(
        "Chat",
        back_populates="goals",
        lazy="joined"
    )
    parent_goal: Mapped["Goal | None"] = relationship(
        "Goal",
        back_populates="sub_goals",
        remote_side=[id],
        lazy="joined"
    )
    sub_goals: Mapped[list["Goal"]] = relationship(
        "Goal",
        back_populates="parent_goal",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Composite index for efficient filtering
    __table_args__ = (
        Index('ix_goals_chat_id_status', 'chat_id', 'status'),
    )

    def __repr__(self):
        return f"<Goal(id={self.id}, chat_id={self.chat_id}, title={self.title}, status={self.status})>"