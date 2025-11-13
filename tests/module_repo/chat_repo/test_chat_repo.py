from app.models import Message,Room,User
from app.repositories.chat_repo import ChatRepository
from app.repositories.room_repo import RoomRepository
from app.repositories.user_repo import UserRepository
from app.schemas.user_schemas import UserCreate



def test_get_message_for_room(chat_repo: ChatRepository,create_table,room_repo: RoomRepository,room_data,user_repo: UserRepository,user_data: UserCreate):
    created_user: User = user_repo.create_user(user_data)
    room_data_with_owner = {
        **room_data,
        'owner_id': created_user.id
    }
    room: Room = room_repo.create_room(room_data_with_owner)
    room.owner = created_user
    assert room is not None
    assert created_user is not None

    message_list: list[Message] = chat_repo.get_message_for_room(room.id)
    assert type(message_list) == list
    assert len(message_list) >= 0
    assert message_list is not None
    assert room.owner.username == user_data['username']


def test_create_message(chat_repo: ChatRepository,create_table,room_repo: RoomRepository,room_data,user_repo: UserRepository,user_data: UserCreate):
    created_user: User = user_repo.create_user(user_data)
    room_data_with_owner = {
        **room_data,
        'owner_id': created_user.id
    }
    room: Room = room_repo.create_room(room_data_with_owner)
    room.owner = created_user
    assert room is not None
    assert created_user is not None

    text = 'hello guys'
    new_message: Message = chat_repo.create_message(room.id,created_user.id,text)
    assert new_message is not None
    assert new_message.user_id == created_user.id
    assert new_message.room_id == room.id

    message_list: list[Message] = chat_repo.get_message_for_room(room.id)
    assert message_list is not None
    assert len(message_list) > 0