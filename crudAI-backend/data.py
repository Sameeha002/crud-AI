from sqlalchemy.orm import Session
from database import SessionLocal
from models import Product
from langchain.tools import tool
# from langchain_tavily import TavilySearch
from tavily import TavilyClient
from dotenv import load_dotenv
import os

load_dotenv()
tavily_client = TavilyClient(api_key = os.getenv("TAVILY_API_KEY"))


@tool
def add_product(title: str, price: int):
   """Add the product"""
   db: Session = SessionLocal()

   product = Product(title = title, price = price)
   db.add(product)
   db.commit()
   db.refresh(product)
   db.close()

   return {
        "id" : product.id,
        "title": product.title,
        "price": product.price
   }

@tool
def update_product(product_id: int, title: str, price: int):
    """Update the product"""
    db: Session = SessionLocal()

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        db.close()
        return {"Product not found"}
    
    product.title = title
    product.price = price
    db.commit()
    db.close()

@tool
def deleteProduct(id : int):
    """Delete the product"""
    db: Session = SessionLocal()

    product = db.query(Product).filter(Product.id == id).first()
    if not product:
        db.close()
        return {"Product not found"}

    
    db.delete(product)
    db.commit()
    db.close()

    return {"message": "Product deleted"}

@tool
def getAllProducts():
    """
    Docstring for getAllProducts
    """
    db: Session = SessionLocal()
    try:
        product = db.query(Product).all()
        return [
            {
                "id": p.id,
                "name": p.title,
                "Price": p.price
            }
            for p in product
        ]
    finally:
        db.close()
    
# tavily_search = TavilySearch(max_results = 2, topic='general', tavily_api_key = os.getenv("TAVILY_API_KEY"))

@tool
def web_search(query: str) -> str:
    """Search the web and return results with source links"""
    response = tavily_client.search(query)

    if not response or "results" not in response:
        return "No Results Found"
    
    summary_text = ""
    sources = []

    for i, result in enumerate(response["results"], start=1):
        summary_text += f"{i}. {result.get('content', '')}\n\n"
        sources.append(result.get('url', ''))

    formatted_response = "\n".join([f"- {url}" for url in sources])
    return f"{summary_text}Sources: \n{formatted_response}\n"


    

    