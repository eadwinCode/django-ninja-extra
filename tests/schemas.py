from pydantic import BaseModel


class UserSchema(BaseModel):
    name: str
    age: int
