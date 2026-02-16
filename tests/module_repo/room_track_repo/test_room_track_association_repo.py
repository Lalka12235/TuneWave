import uuid
from app.infrastructure.db.gateway.room_track_association_gateway import RoomTrackAssociationGateway
from app.infrastructure.db.models import RoomTrackAssociationModel

def test_add_track_and_get_last_order(room_track_repo: RoomTrackAssociationGateway):
    room_id = uuid.uuid4()
    track_id1 = uuid.uuid4()
    user_id = uuid.uuid4()

    assert room_track_repo.get_last_order_in_queue(room_id) == 0

    assoc1 = room_track_repo.add_track_to_queue(
        room_id, 
        track_id1, 
        room_track_repo.get_last_order_in_queue(room_id), 
        user_id
    )
    assert isinstance(assoc1, RoomTrackAssociationModel)
    assert assoc1.room_id == room_id
    assert assoc1.track_id == track_id1
    assert assoc1.order_in_queue == 0

    assert room_track_repo.get_last_order_in_queue(room_id) == 1

    track_id2 = uuid.uuid4()
    assoc2 = room_track_repo.add_track_to_queue(
        room_id, 
        track_id2, 
        room_track_repo.get_last_order_in_queue(room_id), 
        user_id
    )
    assert assoc2.order_in_queue == 1

    queue = room_track_repo.get_queue_for_room(room_id)
    assert len(queue) == 2
    assert [a.order_in_queue for a in queue] == [0, 1]
    assert [a.track_id for a in queue] == [track_id1, track_id2]

def test_get_queue_for_room(room_track_repo: RoomTrackAssociationGateway):
    room_id = uuid.uuid4()
    track_id = uuid.uuid4()
    user_id = uuid.uuid4()

    room_track_repo.add_track_to_queue(
        room_id,
        track_id,
        room_track_repo.get_last_order_in_queue(room_id),
        user_id
    )

    queue = room_track_repo.get_queue_for_room(room_id)
    assert len(queue) == 1
    assert queue[0].room_id == room_id
    assert queue[0].track_id == track_id

def test_remove_track_from_queue(room_track_repo: RoomTrackAssociationGateway):
    room_id = uuid.uuid4()
    track_id = uuid.uuid4()
    user_id = uuid.uuid4()

    room_track_repo.add_track_to_queue(
        room_id,
        track_id,
        room_track_repo.get_last_order_in_queue(room_id),
        user_id
    )

    result = room_track_repo.remove_track_from_queue(room_id, track_id)
    assert result is True

    queue = room_track_repo.get_queue_for_room(room_id)
    assert len(queue) == 0

def test_get_last_order_in_queue(room_track_repo: RoomTrackAssociationGateway):
    room_id = uuid.uuid4()
    
    assert room_track_repo.get_last_order_in_queue(room_id) == 0

    track_ids = [uuid.uuid4() for _ in range(3)]
    user_id = uuid.uuid4()

    for track_id in track_ids:
        room_track_repo.add_track_to_queue(
            room_id,
            track_id,
            room_track_repo.get_last_order_in_queue(room_id),
            user_id
        )

    assert room_track_repo.get_last_order_in_queue(room_id) == 3

def test_remove_nonexistent_track(room_track_repo: RoomTrackAssociationGateway):
    room_id = uuid.uuid4()
    track_id = uuid.uuid4()

    result = room_track_repo.remove_track_from_queue(room_id, track_id)
    assert result is False