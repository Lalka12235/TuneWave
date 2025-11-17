from dishka import make_container, Container, Provider


def provide_set() -> list[Provider]:
    return [

    ]


def get_container() -> Container:
    return make_container(*provide_set())