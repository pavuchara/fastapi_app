from sqlalchemy import (
    Integer,
    String,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    validates,
    relationship,
)

from alchemy.db import Base
from models.services.validators import (
    validate_recipe_cooking_time,
    validate_recipe_ingredient_amount,
)


class Recipe(Base):
    __tablename__ = "recipes"

    # Fields:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(256))
    image: Mapped[str] = mapped_column(String(255), nullable=True)
    text: Mapped[str] = mapped_column(String(1000))
    cooking_time: Mapped[int] = mapped_column(Integer)
    # Relationships:
    author = relationship(
        "models.user.User",
        back_populates="recipe",
    )
    tags = relationship(
        "models.recipe.RecipeTag",
        back_populates="recipe",
        cascade="all, delete-orphan",
    )
    ingredients = relationship(
        "models.recipe.RecipeIngredient",
        back_populates="recipe",
        cascade="all, delete-orphan",
    )
    favorited_by_users = relationship(
        "models.user.UserFavorites",
        back_populates="favoreted_recipes",
        cascade="all, delete-orphan",
    )
    shopping_list_users = relationship(
        "models.user.UserShoppingList",
        back_populates="recipes_in_shopping_list",
        cascade="all, delete-orphan"
    )

    @validates("cooking_time")
    def validate_cooking_time(self, _, value):
        return validate_recipe_cooking_time(value)

    @property
    def tag_list(self):
        return [recipe_tag.tag for recipe_tag in self.tags]


class RecipeTag(Base):
    __tablename__ = "recipe_tag"
    __table_args__ = (UniqueConstraint("recipe_id", "tag_id", name="unique_recipe_tag"),)
    # Fields:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recipe_id: Mapped[int] = mapped_column(Integer, ForeignKey("recipes.id"))
    tag_id: Mapped[int] = mapped_column(Integer, ForeignKey("tags.id"))
    # Relationships:
    recipe = relationship(
        "models.recipe.Recipe",
        foreign_keys=[recipe_id],
        back_populates="tags",
    )
    tag = relationship(
        "models.core.Tag",
        foreign_keys=[tag_id],
        back_populates="tag_recipes",
    )


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredient"
    __table_args__ = (
        UniqueConstraint("recipe_id", "ingredient_id", name="unique_recipe_ingredient"),
    )
    # Fields:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recipe_id: Mapped[int] = mapped_column(Integer, ForeignKey("recipes.id"))
    ingredient_id: Mapped[int] = mapped_column(Integer, ForeignKey("ingredients.id"))
    amount: Mapped[int] = mapped_column(Integer)
    # Relationships:
    recipe = relationship(
        "models.recipe.Recipe",
        foreign_keys=[recipe_id],
        back_populates="ingredients",
    )
    ingredient = relationship(
        "models.core.Ingredient",
        foreign_keys=[ingredient_id],
        back_populates="ingredient_recipes"
    )

    @validates("amount")
    def validate_amount(self, _, value):
        return validate_recipe_ingredient_amount(value)
