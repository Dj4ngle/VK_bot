import typing
from hashlib import sha256

from aiohttp.web_exceptions import HTTPForbidden
from sqlalchemy import text, insert, select

from kts_backend.admin.models import Admin, AdminModel
from kts_backend.base.base_accessor import BaseAccessor

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


class AdminAccessor(BaseAccessor):
    async def get_by_email(self, email: str) -> typing.Optional[Admin]:

        async with self.app.database.session() as session:
            res = await session.execute(
                select(AdminModel).where(AdminModel.email == email)
            )
            result = res.scalars().first()
            if result == []:
                return None
        return result

    async def create_admin(self, email: str, password: str) -> Admin:
        async with self.app.database.session() as session:

            hashed_pass = sha256(password.encode()).hexdigest()
            result = await session.execute(
                insert(AdminModel).values(email=email, password=hashed_pass)
            )
            await session.commit()
            return result
