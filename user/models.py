import uuid

from pydantic import BaseModel, EmailStr
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class User(Base):
    __tablename__ = "user"

    # Mapped, a generic type that indicates a specific Python type within it.
    # mapped_column automatically derives from the annotation
    # But you can always explicitly supply the type in mapped_column to override settings
    # I would advise to at least include Mapped so that linters will catch the typing when working across the repo (otherwise, it would show as type Any on tooltips)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)


# Pydantic models
class UserBaseModel(BaseModel):
    id: uuid.UUID


class NewUserRead(UserBaseModel):
    pass


class UserRead(UserBaseModel):
    email: EmailStr | None = None  # not all users use email for login
    name: str | None = None
