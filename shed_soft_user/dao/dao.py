from sqlalchemy.ext.asyncio import AsyncSession

from shed_soft_user.dao.base import BaseDAO
from shed_soft_user.dao.models import Note, Realm, User


class RealmDAO(BaseDAO[Realm]):
    """DAO для работы с realm."""
    model = Realm

    def __init__(self, session: AsyncSession):
        super().__init__(session)


class UsersDAO(BaseDAO[User]):
    """DAO для работы с пользователями."""
    model = User

    def __init__(self, session: AsyncSession):
        super().__init__(session)


class NotesDAO(BaseDAO[Note]):
    """DAO для работы с заметками."""
    model = Note

    def __init__(self, session: AsyncSession):
        super().__init__(session)
