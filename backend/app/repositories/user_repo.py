from sqlalchemy import select,insert,delete
from app.config.session import Session
from app.models.user import UserModel
from backend.app.schemas.user_schema import UserRegisterSchema,UserLoginSchema
from app.utils.hash import make_hash_pass



class UserRepository:

    @staticmethod
    def get_user(username: str):
        with Session() as session:
            stmt = select(UserModel).where(UserModel.username == username)
            user = session.execute(stmt).scalar_one_or_none()
            return user
        
    @staticmethod
    def register_user(user: UserRegisterSchema):
        with Session() as session:
            hash_pass = make_hash_pass(user.password)

            stmt = insert(UserModel).values(username=user.username,email=user.email,password_hash=hash_pass)
            session.execute(stmt)
            session.commit()
        
    @staticmethod
    def delete_user(user: UserLoginSchema):
        with Session() as session:
            hash_pass = make_hash_pass(user.password)

            stmt = delete(UserModel).where(UserModel.username == user.username,UserModel.password_hash == hash_pass).returning(UserModel.id)
            session.execute(stmt)
            session.commit()