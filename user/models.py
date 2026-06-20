import uuid
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base

if TYPE_CHECKING:
    from role.models import Role


class User(Base):
    __tablename__ = "user"

    # Mapped, a generic type that indicates a specific Python type within it.
    # mapped_column automatically derives from the annotation
    # But you can always explicitly supply the type in mapped_column to override settings
    # I would advise to at least include Mapped so that linters will catch the typing when working across the repo (otherwise, it would show as type Any on tooltips)

    id: Mapped[int] = mapped_column(primary_key=True)
    external_auth_id: Mapped[uuid.UUID] = mapped_column()
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("role.id"))

    role: Mapped["Role"] = relationship(back_populates="users")


# Pydantic models
class UserBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    role_id: int


class NewUserRead(UserBaseModel):
    """Newly registered user which surely has an ID but unser whether email or phone number or something else is used to login... compared to UserRead.

    And again e.g. that email or phone number, may be stored already in the auth instead of our db.
    """

    pass


class UserRead(UserBaseModel):
    email: EmailStr | None = None  # not all users use email for login
    name: str | None = None
