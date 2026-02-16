from app.infrastructure.db.models import Room,User


def test_get_room_by_id(room_repo,room_data,user_repo,user_data):
    created_user: User = user_repo.create_user(user_data)
    room_data_with_owner = {
        **room_data,
        'owner_id': created_user.id
    }
    created: Room = room_repo.create_room(room_data_with_owner)
    assert created is not None

    fetched: Room = room_repo.get_room_by_id(created.id)
    assert fetched is not None
    assert fetched.name == room_data.get('name')
    assert fetched.max_members == room_data.get('max_members')


def test_get_room_by_name(room_repo,room_data,user_repo,user_data):
    created_user: User = user_repo.create_user(user_data)
    room_data_with_owner = {
        **room_data,
        'owner_id': created_user.id
    }
    created: Room = room_repo.create_room(room_data_with_owner)
    assert created is not None

    fetched: Room = room_repo.get_room_by_name(created.name)
    assert fetched is not None
    assert fetched.name == room_data.get('name')
    assert fetched.max_members == room_data.get('max_members')


def test_get_all_rooms(room_repo,room_data,user_repo,user_data):
    created_user: User = user_repo.create_user(user_data)
    room_data_with_owner = {
        **room_data,
        'owner_id': created_user.id
    }
    created: Room = room_repo.create_room(room_data_with_owner)
    assert created is not None

    fetched: list[Room] = room_repo.get_all_rooms()
    assert fetched is not None
    assert len(fetched) > 0


def test_create_room(room_repo,room_data,user_repo,user_data):
    created_user: User = user_repo.create_user(user_data)
    room_data_with_owner = {
        **room_data,
        'owner_id': created_user.id
    }
    created: Room = room_repo.create_room(room_data_with_owner)
    assert created is not None

    fetched: Room = room_repo.get_room_by_id(created.id)
    assert fetched is not None


def test_update_room(room_repo,room_data,user_repo,user_data):
    created_user: User = user_repo.create_user(user_data)
    room_data_with_owner = {
        **room_data,
        'owner_id': created_user.id
    }
    created: Room = room_repo.create_room(room_data_with_owner)
    assert created is not None

    new_name = 'aspirin2'
    updated: Room = room_repo.update_room(created,{'name': new_name})
    assert updated is not None


def test_delete_room(room_repo,room_data,user_repo,user_data):
    created_user: User = user_repo.create_user(user_data)
    room_data_with_owner = {
        **room_data,
        'owner_id': created_user.id
    }
    created: Room = room_repo.create_room(room_data_with_owner)
    assert created is not None

    updated: bool = room_repo.delete_room(created.id)
    assert updated

def test_get_active_rooms(room_repo,room_data,user_repo,user_data):
    created_user: User = user_repo.create_user(user_data)
    room_data_with_owner = {
        **room_data,
        'owner_id': created_user.id
    }
    created: Room = room_repo.create_room(room_data_with_owner)
    assert created is not None

    fetched_list: list[Room] = room_repo.get_active_rooms()
    assert len(fetched_list) == 0


def test_get_owner_room(room_repo,room_data,user_repo,user_data):
    created_user: User = user_repo.create_user(user_data)
    room_data_with_owner = {
        **room_data,
        'owner_id': created_user.id
    }
    created: Room = room_repo.create_room(room_data_with_owner)
    assert created is not None

    fetched: Room = room_repo.get_owner_room(created.id)
    assert fetched.owner_id == created_user.id