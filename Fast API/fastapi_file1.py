from fastapi import FastAPI

app = FastAPI()

products = [
    {
        "id" : 1,
        "name":"shirt",
        "price":10000
    },
    {
        "id" : 2,
        "name":"T - Shirt",
        "price":200
    },
    {
        "id" : 3,
        "name":"Watch",
        "price":10
    },
]

@app.get("/")
def welcome():
    return {"message":"welcome to FastAPI"}



@app.get("/login")
def login():
    return {"message":"user login....!"}
    

@app.get("/products")
def products1():
    return {"product":products}
    
@app.get("/products/{id}")
def product(id : int = 0):
    
    for i in products:
        if i["id"] == id:
            return {"product":i}
    
    return {"Error":"product not found...!",
            "status_code":404
            }
            
    
