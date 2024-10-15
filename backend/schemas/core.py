from pydantic import BaseModel


class TagCreateSchema(BaseModel):
    name: str
    slug: str


class TagRetrieveSchema(TagCreateSchema):
    id: int


class IngredientCreateSchema(BaseModel):
    name: str
    measurement_unit: str


class IngredientRetrieveSchema(IngredientCreateSchema):
    id: int
