from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from pydantic import (
    BaseModel, EmailStr, Field, ValidationError, constr, conint, validator
)

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")
NAME_RE = re.compile(r"^[A-Z][a-zA-Z]{1,}$")
PHONE_RE = re.compile(r"^\+\d-\d{3}-\d{2}-\d{2}$")
PASSWORD_DIGIT_RE = re.compile(r"\d")
PASSWORD_LOWER_RE = re.compile(r"[a-z]")
PASSWORD_UPPER_RE = re.compile(r"[A-Z]")


class UserRegistration(BaseModel):
    username: constr(min_length=3, max_length=20, regex=r"^[A-Za-z0-9_]+$")
    email: EmailStr
    password: constr(min_length=8)
    password_confirm: str
    age: conint(ge=18, le=120)
    registration_date: datetime = Field(default_factory=datetime.utcnow)
    real_name: constr(min_length=2)
    phone: constr(regex=r"^\+\d-\d{3}-\d{2}-\d{2}$")

    @validator("username")
    def validate_username(cls, value: str) -> str:
        if not USERNAME_RE.match(value):
            raise ValueError(
                (
                    "Username должен содержать только латинские буквы,"
                    " цифры и подчеркивание"
                )
            )
        return value

    @validator("password")
    def validate_password(cls, value: str) -> str:
        if not PASSWORD_DIGIT_RE.search(value):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        if not PASSWORD_LOWER_RE.search(value):
            raise ValueError(
                "Пароль должен содержать хотя бы одну строчную букву"
            )
        if not PASSWORD_UPPER_RE.search(value):
            raise ValueError(
                "Пароль должен содержать хотя бы одну заглавную букву"
            )
        return value

    @validator("password_confirm")
    def validate_password_confirm(
        cls, value: str, values: dict[str, Any]
    ) -> str:
        if "password" in values and value != values["password"]:
            raise ValueError("Пароли не совпадают")
        return value

    @validator("real_name")
    def validate_real_name(cls, value: str) -> str:
        if not NAME_RE.match(value):
            raise ValueError(
                (
                    "Имя должно начинаться с заглавной буквы"
                    " и содержать минимум 2 буквы"
                )
            )
        return value

    @validator("phone")
    def validate_phone(cls, value: str) -> str:
        if not PHONE_RE.match(value):
            raise ValueError("Телефон должен быть в формате +X-XXX-XX-XX")
        return value

    def serialize(self) -> dict[str, Any]:
        return self.dict(exclude={"password_confirm"})


def register_user(data: dict[str, Any]) -> UserRegistration | list[str]:
    try:
        return UserRegistration(**data)
    except ValidationError as exc:
        return [error["msg"] for error in exc.errors()]


def create_recursive_model() -> type[BaseModel]:
    class NestedNode(BaseModel):
        data: str
        child: "NestedNode" | None = None

    NestedNode.update_forward_refs()
    return NestedNode
