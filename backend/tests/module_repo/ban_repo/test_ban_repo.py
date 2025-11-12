from app.repositories.ban_repo import BanRepository
import uuid


def test_get_bans_by_admin(ban_repo: BanRepository, user_data1: dict, user_data2: dict):
    room_id = uuid.uuid4()
    ban_repo.add_ban(
        room_id=room_id,
        ban_user_id=user_data2["id"],
        by_ban_user_id=user_data1["id"],
        reason="Test ban",
    )

    bans = ban_repo.get_bans_by_admin(user_data1["id"])

    assert len(bans) == 1
    assert bans[0].by_ban_user_id == user_data1["id"]
    assert bans[0].ban_user_id == user_data2["id"]


def test_get_bans_on_user(ban_repo: BanRepository, user_data1: dict, user_data2: dict):
    room_ids = [uuid.uuid4(), uuid.uuid4()]
    for room_id in room_ids:
        ban_repo.add_ban(
            room_id=room_id,
            ban_user_id=user_data2["id"],
            by_ban_user_id=user_data1["id"],
            reason=f"Test ban for room {room_id}",
        )

    bans = ban_repo.get_bans_on_user(user_data2["id"])

    assert len(bans) == 2
    assert all(ban.ban_user_id == user_data2["id"] for ban in bans)


def test_add_ban(ban_repo: BanRepository, user_data1: dict, user_data2: dict):
    room_id = uuid.uuid4()
    ban = ban_repo.add_ban(
        room_id=room_id,
        ban_user_id=user_data2["id"],
        by_ban_user_id=user_data1["id"],
        reason="Test ban reason",
    )

    assert ban is not None
    assert ban.ban_user_id == user_data2["id"]
    assert ban.by_ban_user_id == user_data1["id"]
    assert ban.room_id == room_id
    assert ban.reason == "Test ban reason"


def test_remove_ban_local(ban_repo: BanRepository, user_data1: dict, user_data2: dict):
    room_id = uuid.uuid4()
    ban_repo.add_ban(
        room_id=room_id,
        ban_user_id=user_data2["id"],
        by_ban_user_id=user_data1["id"],
        reason="Test local ban",
    )

    result = ban_repo.remove_ban_local(room_id, user_data2["id"])

    assert result is True
    assert ban_repo.is_user_banned_local(user_data2["id"], room_id) is None


def test_remove_ban_global(ban_repo: BanRepository, user_data1: dict, user_data2: dict):
    ban_repo.add_ban(
        room_id=None,
        ban_user_id=user_data2["id"],
        by_ban_user_id=user_data1["id"],
        reason="Test global ban",
    )

    result = ban_repo.remove_ban_global(user_data2["id"])

    assert result is True
    assert ban_repo.is_user_banned_global(user_data2["id"]) is None


def test_is_user_banned_global(
    ban_repo: BanRepository, user_data1: dict, user_data2: dict
):
    ban_repo.add_ban(
        room_id=None,
        ban_user_id=user_data2["id"],
        by_ban_user_id=user_data1["id"],
        reason="Test global ban",
    )

    result = ban_repo.is_user_banned_global(user_data2["id"])

    assert result is not None
    assert result.ban_user_id == user_data2["id"]
    assert result.room_id is None


def test_is_user_banned_local(
    ban_repo: BanRepository, user_data1: dict, user_data2: dict
):
    room_id = uuid.uuid4()
    ban_repo.add_ban(
        room_id=room_id,
        ban_user_id=user_data2["id"],
        by_ban_user_id=user_data1["id"],
        reason="Test local ban",
    )

    result = ban_repo.is_user_banned_local(user_data2["id"], room_id)

    assert result is not None
    assert result.ban_user_id == user_data2["id"]
    assert result.room_id == room_id


def test_no_bans_exist(ban_repo: BanRepository, user_data1: dict):
    room_id = uuid.uuid4()

    global_ban = ban_repo.is_user_banned_global(user_data1["id"])
    local_ban = ban_repo.is_user_banned_local(user_data1["id"], room_id)

    assert global_ban is None
    assert local_ban is None
