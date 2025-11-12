import uuid
from app.repositories.member_room_association_repo import (
    MemberRoomAssociationRepository,
)
from app.repositories.room_repo import RoomRepository
from app.models.member_room_association import Member_room_association


def test_add_member(
    member_room_repo: MemberRoomAssociationRepository, user_data1: dict
):
    room_id = uuid.uuid4()

    member = member_room_repo.add_member(
        user_id=user_data1["id"], room_id=room_id, role="member"
    )

    assert isinstance(member, Member_room_association)
    assert member.user_id == user_data1["id"]
    assert member.room_id == room_id
    assert member.role == "member"


def test_remove_member(
    member_room_repo: MemberRoomAssociationRepository, user_data1: dict
):
    room_id = uuid.uuid4()

    member_room_repo.add_member(
        user_id=user_data1["id"], room_id=room_id, role="member"
    )

    result = member_room_repo.remove_member(user_data1["id"], room_id)
    assert result is True

    association = member_room_repo.get_association_by_ids(user_data1["id"], room_id)
    assert association is None


def test_get_association_by_ids(
    member_room_repo: MemberRoomAssociationRepository, user_data1: dict
):
    room_id = uuid.uuid4()

    member_room_repo.add_member(
        user_id=user_data1["id"], room_id=room_id, role="member"
    )

    association = member_room_repo.get_association_by_ids(user_data1["id"], room_id)

    assert association is not None
    assert association.user_id == user_data1["id"]
    assert association.room_id == room_id


def test_get_members_by_room_id(
    member_room_repo: MemberRoomAssociationRepository,
    user_data1: dict,
    user_data2: dict,
):
    room_id = uuid.uuid4()

    member_room_repo.add_member(user_data1["id"], room_id, "member")
    member_room_repo.add_member(user_data2["id"], room_id, "member")

    members = member_room_repo.get_members_by_room_id(room_id)

    assert len(members) == 2
    member_ids = [m.user_id for m in members]
    assert user_data1["id"] in member_ids
    assert user_data2["id"] in member_ids


def test_get_rooms_by_user_id(
    member_room_repo: MemberRoomAssociationRepository,
    user_data1: dict,
    room_repo: RoomRepository,
    room_data,
):
    length = 3
    user_id = uuid.uuid4()
    room_data_with_owner = {
        **room_data,
        'owner_id': user_id
    }

    for i in range(length):
        room_data_with_owner['name'] = room_data_with_owner.get('name') + str(i)
        new_room = room_repo.create_room(room_data_with_owner)
        member_room_repo.add_member(user_data1["id"], new_room.id, "member")

    rooms = member_room_repo.get_rooms_by_user_id(user_data1["id"])

    assert len(rooms) == length


def test_update_role(
    member_room_repo: MemberRoomAssociationRepository, user_data1: dict
):
    room_id = uuid.uuid4()

    member_room_repo.add_member(user_data1["id"], room_id, "member")

    updated = member_room_repo.update_role(room_id, user_data1["id"], "moderator")

    assert updated is not None
    assert updated.role == "moderator"

    association = member_room_repo.get_association_by_ids(user_data1["id"], room_id)
    assert association.role == "moderator"


def test_get_member_room_association(
    member_room_repo: MemberRoomAssociationRepository, user_data1: dict
):
    room_id = uuid.uuid4()

    member_room_repo.add_member(user_data1["id"], room_id, "member")

    association = member_room_repo.get_member_room_association(
        room_id, user_data1["id"]
    )

    assert association is not None
    assert association.user_id == user_data1["id"]
    assert association.room_id == room_id
    assert association.role == "member"


def test_remove_nonexistent_member(member_room_repo: MemberRoomAssociationRepository):
    result = member_room_repo.remove_member(uuid.uuid4(), uuid.uuid4())
    assert result is False


def test_get_nonexistent_association(member_room_repo: MemberRoomAssociationRepository):
    association = member_room_repo.get_association_by_ids(uuid.uuid4(), uuid.uuid4())
    assert association is None
