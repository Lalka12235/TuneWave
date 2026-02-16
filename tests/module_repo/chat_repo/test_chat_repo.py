from app.infrastructure.db.models import Message,Room,User
from app.infrastructure.db.gateway.chat_gateway import ChatGateway
from app.infrastructure.db.gateway.room_gateway import RoomGateway
from app.infrastructure.db.gateway.user_gateway import UserGateway
from app.presentation.schemas.user_schemas import UserCreate



def test_get_message_for_room(chat_repo: ChatGateway,create_table,room_repo: RoomGateway,room_data,user_repo: UserGateway,user_data: UserCreate):
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
    assert isinstance(type(message_list),list)
    assert len(message_list) >= 0
    assert message_list is not None
    assert room.owner.username == user_data['username']


def test_create_message(chat_repo: ChatGateway,create_table,room_repo: RoomGateway,room_data,user_repo: UserGateway,user_data: UserCreate):
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