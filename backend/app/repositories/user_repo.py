from sqlalchemy import select,insert,delete
from app.config.session import AsyncSessionLocal
from app.models.user import UserModel
from backend.app.schemas.user_schema import UserRegisterSchema,UserLoginSchema
from app.utils.hash import make_hash_pass



class UserRepository:

    @staticmethod
    async def get_user(username: str):
        async with AsyncSessionLocal() as session:
            stmt = select(UserModel).where(UserModel.username == username)
            user = await session.execute(stmt).scalar_one_or_none()
            return user
        
    @staticmethod
    async def register_user(user: UserRegisterSchema):
        async with AsyncSessionLocal() as session:
            hash_pass = make_hash_pass(user.password)

            stmt = insert(UserModel).values(username=user.username,password_hash=hash_pass)
            await session.execute(stmt)
            await session.commit()
        
    @staticmethod
    async def delete_user(user: UserLoginSchema):
        async with AsyncSessionLocal() as session:
            hash_pass = make_hash_pass(user.password)

            stmt = delete(UserModel).where(UserModel.username == user.username,UserModel.password_hash == hash_pass).returning(UserModel.id)
            await session.execute(stmt)
            await session.commit()