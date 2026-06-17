from db.database import DBSession
from user.models import NewUserRead, User


async def create_user(db_session: DBSession, uid: str) -> NewUserRead:
    """Create user."""
    new_user = User(
        id=uid,
    )

    db_session.add(new_user)
    await db_session.commit()

    return NewUserRead(id=new_user.id)
