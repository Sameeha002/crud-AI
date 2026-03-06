from fastapi import FastAPI
from database import SessionLocal, Base, engine
from models import Product, Feedback, Message, ChatThread
from routes import user, assistant, assistant_ws
from fastapi.middleware.cors import CORSMiddleware
from routes import editMessages as messages_router




app = FastAPI(title="CRUD with AI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.create_all(bind=engine)
@app.get("/")
def read_root():
    return {"message": "Welcome to CRUD AI"}

@app.get('/products')
def get_all_products():
    db = SessionLocal()
    products = db.query(Product).all()
    db.close()
    return products

app.include_router(user.router)
# app.include_router(assistant.router)
app.include_router(assistant_ws.router)
app.include_router(messages_router.router)












# @app.get('/products/{id}')
# def productDetail(id: int):
#     lookup = {d['id'] : d for d in products_list}
#     res = lookup.get(id,{'Message':'Data not Found'})
#     return res

# @app.post('/add_product')
# def add_new_prod(prod : Item):
#     new_prod_id = max([p['id'] for p in products_list]) + 1

#     new_prod = {
#         'id' : new_prod_id,
#         'title' : prod['title'],
#         'price' : prod['price']
#     }

#     products_list.append(new_prod)
#     return products_list

# @app.put('/products/{id}')
# def update_product(id: int, updated_item: Item):
#     for product in products_list:
#         if product['id'] == id:
#             product['title'] = updated_item.title
#             product['price'] = updated_item.price
#             return product

#     return {'message': 'Data not Found'}

# @app.delete('/products/{id}')
# def deleteProduct(id : int):
#     for index,prod in enumerate(products_list):
#         if prod['id'] == id:
#             products_list.pop(index)
#             return products_list
#     return {'Message':'Data not Found'}