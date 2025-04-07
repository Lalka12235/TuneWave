from app.repositories.user_repo import UserRepository
from backend.app.schemas.user_schema import UserRegisterSchema, UserLoginSchema
from fastapi import HTTPException, status


class UserServices:

    @staticmethod
    async def get_user(username: str):
        user = await UserRepository.get_user(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )
        return {'message': 'User found', 'detail': username}

    @staticmethod
    async def register_user(user: UserRegisterSchema):
        existing_user =await UserRepository.get_user(user.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='User already exists'
            )

        user_id =await UserRepository.register_user(user)
        return {'message': 'Account created', 'user_id': user_id}

    @staticmethod
    async def delete_user(user: UserLoginSchema):
        deleted_user =await UserRepository.delete_user(user)
        if not deleted_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found or incorrect password'
            )

        return {'message': 'Account deleted', 'user_id': deleted_user}
