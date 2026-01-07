from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shed_soft_user.dao.base_model import Base


class User(Base):
    __tablename__ = "users"

    # Переопределяем id из Base для использования строкового типа (UUID из Keycloak)
    id: Mapped[str] = mapped_column(primary_key=True, autoincrement=False, init=True)
    email: Mapped[str] = mapped_column(unique=True)
    email_verified: Mapped[bool] = mapped_column(default=False)
    name: Mapped[str] = mapped_column(default="")
    preferred_username: Mapped[str] = mapped_column(default="")
    given_name: Mapped[str] = mapped_column(default="")
    family_name: Mapped[str] = mapped_column(default="")
    realm_name: Mapped[str] = mapped_column(default="")
    notes: Mapped[list["Note"]] = relationship(
        back_populates="user",
        init=False,
        default_factory=list
    )


class Note(Base):
    __tablename__ = "notes"

    # Используем id из Base (int с автоинкрементом)
    title: Mapped[str] = mapped_column(init=True)
    content: Mapped[str] = mapped_column(init=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), init=True)
    user: Mapped["User"] = relationship(
        back_populates="notes",
        init=False
    )
