import re

from email_validator import validate_email, EmailNotValidError

from models.services.exceptions import UserValidationException


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
