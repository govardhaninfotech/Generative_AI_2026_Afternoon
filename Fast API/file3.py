from fastapi import FastAPI
from pydantic import BaseModel
users = []

app = FastAPI()

class User(BaseModel):
    id : int
    name : str
    email : str
    phone : int


@app.get("/")
def welcome():
    return {
        "message":"welcome to server..!"
    }
    
@app.get("/users")
def display_user():
    return {"users":users}

# ---------------------------------------------------
# @app.post("/users")
# def add_user(u:User):
#     print(u)
#     print(type(u))
    
#     user = u.dict()
#     print(user)
#     print(type(user))
#     return {"message":"user added...!",
#             "status": 201}
# ---------------------------------------------------

@app.post("/users")
def add_user(u:User):
    
    user = u.dict()
    print(user)
    users.append(user)
    user
    return {"message":f"user added...! welcome {user["name"]}",
            "status": 201}
    

@app.patch("/users/{id}")
def updt_user(u:User):
    return {"message":"user updated..!"}


@app.delete("/users/{id}")
def det_user(u:User):
    return {"message":"user updated..!"}