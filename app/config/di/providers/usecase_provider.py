from dishka import Provider,Scope,provide_all,provide
from app.application.commands.user import CreateUser,UpdateUser,DeleteUser,ReadUser
from app.application.commands.track import CreateTrack,ReadTrack,DeleteTrack


class ServiceProvider(Provider):
    scope = Scope.REQUEST

    interactors = provide_all(
        CreateUser,
        UpdateUser,
        DeleteUser,
        ReadUser,
        CreateTrack,
        ReadTrack,
        DeleteTrack,
        
    )