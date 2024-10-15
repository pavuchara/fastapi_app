from sqlalchemy import (
    Integer,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    validates,
    relationship,
)

from slugify import slugify

from alchemy.db import Base


class Tag(Base):
    __tablename__ = "tags"
    # Fields:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(32), unique=True)
    slug: Mapped[str] = mapped_column(String(32), unique=True)
    # Relationships:
    tag_recipes = relationship(
        "models.recipe.RecipeTag",
        back_populates="tag",
    )

    @validates("slug")
    def validate_slug(self, _, value):
        return slugify(value)


class Ingredient(Base):
    __tablename__ = "ingredients"
    # Fields:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    measurement_unit: Mapped[str] = mapped_column(String(64))
    # Relationships:
    ingredient_recipes = relationship(
        "models.recipe.RecipeIngredient",
        back_populates="ingredient",
    )
