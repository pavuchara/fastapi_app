import re

from email_validator import validate_email, EmailNotValidError

from models.services.exceptions import (
    UserValidationException,
    RecipeValidationException,
)


USERNAME_REGEX = r'^[\w.@+-]+\Z'


def validate_user_email(email: str):
    try:
        emailinfo = validate_email(email)
        return emailinfo.normalized
    except EmailNotValidError:
        raise UserValidationException("Некорректный email")


def validate_username(username: str):
    if username.lower() == "me":
        raise UserValidationException("В кач-ве username нельзя выбрать `me`")
    if not re.match(USERNAME_REGEX, username):
        raise UserValidationException("Только буквы, цифры и @/./+/-/_ разрешены.")
    return username


def validate_recipe_cooking_time(value: int):
    if not (1 <= value <= 1000):
        raise RecipeValidationException("Время готовки должно быть от 1 до 1000 минут.")
    return value


def validate_recipe_ingredient_amount(value: int):
    if not (1 <= value <= 1000):
        raise RecipeValidationException
    return value
