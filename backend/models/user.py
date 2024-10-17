from sqlalchemy import (
    Integer,
    String,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    TEXT,
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
    avatar: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    # Relationships:
    recipe = relationship(
        "models.recipe.Recipe",
        back_populates="author",
        cascade="all, delete-orphan",
    )
    token = relationship(
        "UserBaseToken",
        uselist=False,
        back_populates="user",
        cascade="all, delete-orphan",
    )
    subscriptions = relationship(
        "UserSubscription",
        foreign_keys="[UserSubscription.user_id]",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    followers = relationship(
        "UserSubscription",
        foreign_keys="[UserSubscription.following_id]",
        back_populates="following",
        cascade="all, delete-orphan",
    )
    user_favorites = relationship(
        "UserFavorites",
        foreign_keys="[UserFavorites.user_id]",
        back_populates="favoreted_users",
        cascade="all, delete-orphan",
    )
    shopping_list = relationship(
        "UserShoppingList",
        foreign_keys="[UserShoppingList.user_id]",
        back_populates="users_shopped",
        cascade="all, delete-orphan"
    )

    @validates("email")
    def validate_email(self, _, value):
        return validate_user_email(value)

    @validates("username")
    def validate_usernmae(self, _, value):
        return validate_username(value)

    @classmethod
    def some(cls):
        return True


class UserBaseToken(Base):
    __tablename__ = "users_tokens"
    # Table fields:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    token: Mapped[str] = mapped_column(String, unique=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    # Relationships:
    user = relationship("models.user.User", back_populates="token")


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    __table_args__ = (
        UniqueConstraint("user_id", "following_id", name="unique_follow"),
        CheckConstraint("user_id != following_id"),
    )
    # Table fields:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    following_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    # Relationships:
    user = relationship(
        "models.user.User",
        foreign_keys=[user_id],
        back_populates="subscriptions",
    )
    following = relationship(
        "models.user.User",
        foreign_keys=[following_id],
        back_populates="followers",
    )


class UserFavorites(Base):
    __tablename__ = "user_favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "recipe_id", name="unique_user_favorites"),
    )
    # Fields:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    recipe_id: Mapped[int] = mapped_column(Integer, ForeignKey("recipes.id"))
    # Relationsips:
    favoreted_users = relationship(
        "models.user.User",
        foreign_keys=[user_id],
        back_populates="user_favorites"
    )
    favoreted_recipes = relationship(
        "models.recipe.Recipe",
        foreign_keys=[recipe_id],
        back_populates="favorited_by_users"
    )


class UserShoppingList(Base):
    __tablename__ = "user_shopping_list"
    __table_args__ = (
        UniqueConstraint("user_id", "recipe_id", name="unique_user_shopping_list"),
    )
    # Fields:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    recipe_id: Mapped[int] = mapped_column(Integer, ForeignKey("recipes.id"))
    # Relationships:
    users_shopped = relationship(
        "models.user.User",
        foreign_keys=[user_id],
        back_populates="shopping_list"
    )
    recipes_in_shopping_list = relationship(
        "models.recipe.Recipe",
        foreign_keys=[recipe_id],
        back_populates="shopping_list_users",
    )
