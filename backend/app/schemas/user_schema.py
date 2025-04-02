from pydantic import BaseModel

class UserRegisterSchema(BaseModel):
    model_config = {'extra':'forbid'}

    username:str
    email: str
    password: str

class UserLoginSchema(BaseModel):
    model_config = {'extra':'forbid'}

    username:str
    password: str