from pydantic import BaseModel

from schemas.core import TagRetrieveSchema
from schemas.user import UserRetrieveSchema


class RecipeIngredientCreateSchema(BaseModel):
    id: int
    amount: int


class RecipeCreateSchema(BaseModel):
    name: str
    image: str | None
    text: str
    cooking_time: int
    tags: list[int]
    ingredients: list[RecipeIngredientCreateSchema]


class RecipeIngredientSchema(BaseModel):
    id: int
    name: str
    measurement_unit: str
    amount: int


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
