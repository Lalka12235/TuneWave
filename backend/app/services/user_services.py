from app.repositories.user_repo import UserRepository
from backend.app.schemas.user_schema import UserRegisterSchema, UserLoginSchema
from fastapi import HTTPException, status


class UserServices:

    @staticmethod
    def get_user(username: str):
        user = UserRepository.get_user(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )
        return {'message': 'User found', 'detail': username}

    @staticmethod
    def register_user(user: UserRegisterSchema):
        existing_user = UserRepository.get_user(user.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='User already exists'
            )

        user_id = UserRepository.register_user(user)
        return {'message': 'Account created', 'user_id': user_id}

    @staticmethod
    def delete_user(user: UserLoginSchema):
        deleted_user = UserRepository.delete_user(user)
        if not deleted_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found or incorrect password'
            )

        return {'message': 'Account deleted', 'user_id': deleted_user}
