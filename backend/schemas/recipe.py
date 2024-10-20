from pydantic import (
    BaseModel,
    Field,
)

from schemas.core import TagRetrieveSchema
from schemas.user import UserRetrieveSchema


class RecipeIngredientCreateSchema(BaseModel):
    id: int
    amount: int


class RecipeCreateSchema(BaseModel):
    name: str = Field(max_length=256)
    image: str | None
    text: str = Field(max_length=1000)
    cooking_time: int = Field(ge=1, le=1000)
    tags: list[int]
    ingredients: list[RecipeIngredientCreateSchema]


class RecipeIngredientSchema(BaseModel):
    id: int
    name: str = Field(max_length=128)
    measurement_unit: str
    amount: int = Field(ge=1, le=10000)


class RecipeRetrieveSchema(BaseModel):
    id: int
    tags: list[TagRetrieveSchema]
    author: UserRetrieveSchema
    ingredients: list[RecipeIngredientSchema]
    name: str
    image: str | None
    text: str
    cooking_time: int
    is_favorited: bool = False
    is_in_shopping_cart: bool = False


class RecipeSimpleRetriveSchema(BaseModel):
    id: int
    name: str
    image: str | None
    cooking_time: int
