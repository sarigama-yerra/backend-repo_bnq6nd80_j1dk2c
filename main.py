import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database import db, create_document, get_documents
from schemas import Product as ProductSchema, Order as OrderSchema

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def serialize_doc(doc: dict):
    if not doc:
        return doc
    d = dict(doc)
    if "_id" in d:
        d["id"] = str(d.pop("_id"))
    # Convert datetime to isoformat
    for k, v in list(d.items()):
        if hasattr(v, "isoformat"):
            d[k] = v.isoformat()
    return d


@app.get("/")
def read_root():
    return {"message": "Saree Store API is running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
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
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
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
    return response


# --------- Product Endpoints ---------

class CreateProduct(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
    image_url: Optional[str] = None
    color: Optional[str] = None
    fabric: Optional[str] = None


@app.get("/api/products")
def list_products():
    try:
        products = get_documents("product")
        if len(products) == 0:
            # Seed sample products on first run
            samples: List[CreateProduct] = [
                CreateProduct(
                    title="Kanjivaram Silk Saree",
                    description="Handwoven zari border, traditional elegance.",
                    price=129.0,
                    category="Silk",
                    image_url="https://images.unsplash.com/photo-1617727553252-6589b89e0ee1?q=80&w=1200&auto=format&fit=crop",
                    color="Maroon",
                    fabric="Silk",
                ),
                CreateProduct(
                    title="Banarasi Brocade Saree",
                    description="Rich motifs with intricate gold threadwork.",
                    price=149.0,
                    category="Banarasi",
                    image_url="https://images.unsplash.com/photo-1610030469975-179a5c1a7109?q=80&w=1200&auto=format&fit=crop",
                    color="Emerald",
                    fabric="Silk",
                ),
                CreateProduct(
                    title="Chiffon Party Wear Saree",
                    description="Lightweight drape with subtle shimmer.",
                    price=89.0,
                    category="Chiffon",
                    image_url="https://images.unsplash.com/photo-1503342217505-b0a15cf70489?q=80&w=1200&auto=format&fit=crop",
                    color="Rose Gold",
                    fabric="Chiffon",
                ),
                CreateProduct(
                    title="Cotton Handloom Saree",
                    description="Breathable comfort with artisanal charm.",
                    price=69.0,
                    category="Cotton",
                    image_url="https://images.unsplash.com/photo-1512436991641-6745cdb1723f?q=80&w=1200&auto=format&fit=crop",
                    color="Indigo",
                    fabric="Cotton",
                ),
                CreateProduct(
                    title="Georgette Designer Saree",
                    description="Flowy silhouette with sequin accents.",
                    price=109.0,
                    category="Georgette",
                    image_url="https://images.unsplash.com/photo-1515378791036-0648a3ef77b2?q=80&w=1200&auto=format&fit=crop",
                    color="Black",
                    fabric="Georgette",
                ),
            ]
            for s in samples:
                create_document("product", ProductSchema(**s.model_dump()))
            products = get_documents("product")
        return [serialize_doc(p) for p in products]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/products")
def create_product(product: CreateProduct):
    try:
        pid = create_document("product", ProductSchema(**product.model_dump()))
        doc = db["product"].find_one({"_id": db["product"]._Database__client.codec_options.document_class.objectid_class(pid)})
        # Fallback: just return id
        return {"id": pid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------- Order Endpoints ---------

@app.post("/api/orders")
def create_order(order: OrderSchema):
    try:
        order_id = create_document("order", order)
        return {"id": order_id, "status": "received", "created_at": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
