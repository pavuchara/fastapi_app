from pydantic import (
    BaseModel,
    Field,
)


class TagCreateSchema(BaseModel):
    name: str = Field(max_length=32)
    slug: str = Field(max_length=32)


class TagRetrieveSchema(TagCreateSchema):
    id: int


class IngredientCreateSchema(BaseModel):
    name: str = Field(max_length=128)
    measurement_unit: str = Field(max_length=32)


class IngredientRetrieveSchema(IngredientCreateSchema):
    id: int
