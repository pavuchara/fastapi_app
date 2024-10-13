from sqlalchemy import (
    Integer,
    String,
    ForeignKey,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    validates,
    relationship,
)

from alchemy.db import Base
from .services.validators import (
    validate_user_email,
    validate_username,
)


class User(Base):
    __tablename__ = "users"
    # Table fields:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    username: Mapped[str] = mapped_column(String(150), unique=True)
    password: Mapped[str] = mapped_column(String(150))
    first_name: Mapped[str] = mapped_column(String(150))
    last_name: Mapped[str] = mapped_column(String(150))
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    # Relationships:
    token = relationship(
        "UserBaseToken",
        uselist=False,
        back_populates="user",
        cascade="all, delete-orphan",
    )

    @validates("email")
    def validate_email(self, _, value):
        return validate_user_email(value)

    @validates("username")
    def validate_usernmae(self, _, value):
        return validate_username(value)


class UserBaseToken(Base):
    __tablename__ = "users_tokens"
    # Table fields
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    token: Mapped[str] = mapped_column(String, unique=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    # Relationships:
    user = relationship("models.user.User", back_populates="token")