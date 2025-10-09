"""
Pydantic — это библиотека для валидации и сериализации данных с помощью Python-типов.
Она позволяет описывать структуру данных в виде классов и автоматически:
"""

from pydantic import BaseModel, field_validator

class User(BaseModel):
    id: int
    name: str
    age: int
    is_active: bool = True   # значение по умолчанию

    @field_validator("age")
    def age_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Возраст должен быть положительным")
        return v

user = User(id="1", name="Alex", age=10) # автоматически преобразовал str → int
print(user)
print(user.name)

print(user.model_dump())       # dict
print(user.model_dump_json())  # JSON