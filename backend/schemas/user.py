from fastapi import HTTPException, status
from pydantic import (
    BaseModel,
    Field,
    ValidationInfo,
    field_validator,
)

from models.services.exceptions import UserValidationException
from models.services.validators import (
    validate_user_email,
    validate_username,
)


class UserCreationSchema(BaseModel):
    email: str = Field(max_length=254)
    username: str = Field(max_length=150)
    password: str = Field(max_length=150)
    first_name: str = Field(max_length=150)
    last_name: str = Field(max_length=150)

    @field_validator("email")
    @classmethod
    def validate_email_field(cls, value: str, info: ValidationInfo):
        try:
            email = validate_user_email(value)
            return email
        except UserValidationException as e:
            raise HTTPException(
                detail={info.field_name: str(e)},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    @field_validator("username")
    @classmethod
    def validate_username_field(cls, value, info: ValidationInfo):
        try:
            validate_username(value)
            return value
        except UserValidationException as e:
            raise HTTPException(
                detail={info.field_name: str(e)},
                status_code=status.HTTP_400_BAD_REQUEST,
            )


class UserRetrieveSchema(BaseModel):
    id: int
    email: str
    username: str
    first_name: str
    last_name: str
    avatar: str | None
    is_subscribed: bool = False


class RecipeSimpleRetriveSchema(BaseModel):
    id: int
    name: str
    image: str | None
    cooking_time: int


class UserWithRecipesSchema(UserRetrieveSchema):
    recipes: list[RecipeSimpleRetriveSchema]


class UserPasswordChangeSchema(BaseModel):
    new_password: str = Field(max_length=150)
    current_password: str = Field(max_length=150)


class UserAvatarSchema(BaseModel):
    avatar: str
