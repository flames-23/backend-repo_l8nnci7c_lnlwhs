import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import Product, Order

app = FastAPI(title="dyfn API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "dyfn backend is running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from dyfn backend!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# API models
class ProductFilter(BaseModel):
    category: Optional[str] = None
    search: Optional[str] = None

@app.get("/api/products", response_model=List[dict])
def list_products(category: Optional[str] = None, search: Optional[str] = None, limit: int = 100):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    query = {}
    if category:
        query["category"] = category
    if search:
        # basic text search across title/description
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]
    products = get_documents("product", query, limit)
    # Convert ObjectId to string
    for p in products:
        if "_id" in p:
            p["id"] = str(p.pop("_id"))
    return products

@app.post("/api/products")
def create_product(product: Product):
    try:
        inserted_id = create_document("product", product)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/orders")
def create_order(order: Order):
    try:
        inserted_id = create_document("order", order)
        return {"id": inserted_id, "status": "received"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/seed")
def seed_products():
    """Seed initial t-shirt and hoodie products if none exist."""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        count = db["product"].count_documents({})
        if count > 0:
            return {"seeded": False, "message": "Products already exist"}
        docs = [
            {
                "title": "Classic DYFN Tee",
                "description": "Premium cotton t-shirt with DYFN logo.",
                "price": 24.99,
                "category": "tshirt",
                "image": "https://images.unsplash.com/photo-1512436991641-6745cdb1723f?q=80&w=1200&auto=format&fit=crop",
                "in_stock": True,
                "sizes": ["S","M","L","XL"],
            },
            {
                "title": "Oversized DYFN Tee",
                "description": "Relaxed fit, ultra-soft fabric.",
                "price": 29.99,
                "category": "tshirt",
                "image": "https://images.unsplash.com/photo-1520975916090-3105956dac38?q=80&w=1200&auto=format&fit=crop",
                "in_stock": True,
                "sizes": ["S","M","L","XL"],
            },
            {
                "title": "DYFN Essential Hoodie",
                "description": "Midweight fleece hoodie for everyday wear.",
                "price": 49.99,
                "category": "hoodie",
                "image": "https://images.unsplash.com/photo-1544441893-675973e31985?q=80&w=1200&auto=format&fit=crop",
                "in_stock": True,
                "sizes": ["S","M","L","XL"],
            },
            {
                "title": "DYFN Heavyweight Hoodie",
                "description": "Thick, cozy, perfect for cold days.",
                "price": 59.99,
                "category": "hoodie",
                "image": "https://images.unsplash.com/photo-1548883354-7622d03aca9b?q=80&w=1200&auto=format&fit=crop",
                "in_stock": True,
                "sizes": ["S","M","L","XL"],
            },
        ]
        for d in docs:
            _ = db["product"].insert_one({**d})
        return {"seeded": True, "count": len(docs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
