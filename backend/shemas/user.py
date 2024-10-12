from typing import Optional

from fastapi import HTTPException, status
from pydantic import (
    BaseModel,
    ValidationInfo,
    field_validator,
)

from models.services.exceptions import UserValidationException
from models.services.validators import (
    validate_user_email,
    validate_username,
)


class UserCreationSchema(BaseModel):
    email: str
    username: str
    password: str
    first_name: str
    last_name: str

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


class UserRetriveSchema(BaseModel):
    id: int
    email: str
    username: str
    first_name: str
    last_name: str


class PaginatedUserRetriveSchema(BaseModel):
    count: int
    next: Optional[str]
    previous: Optional[str]
    results: list[UserRetriveSchema]
