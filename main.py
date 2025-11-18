import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from schemas import Testimonial, BeforeAfter, ContactMessage, Surgery
from database import db, create_document, get_documents

app = FastAPI(title="Bariatric & General Surgery API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Surgeon site backend is running"}


@app.get("/api/surgeries", response_model=List[Surgery])
def list_surgeries():
    """Return list of surgeries (bariatric + general).
    Uses DB if collection exists, otherwise returns a curated default list.
    """
    try:
        items = []
        if db is not None:
            items = get_documents("surgery")
            # Convert Mongo docs to simple dicts
            items = [
                {
                    "name": i.get("name"),
                    "type": i.get("type"),
                    "description": i.get("description"),
                }
                for i in items
            ]
        if items:
            return items
    except Exception:
        # Fall back to defaults if db not available
        pass

    # Default curated list
    return [
        {"name": "Лапароскопическое рукавное гастрошунтирование", "type": "bariatric", "description": "Снижение веса за счёт уменьшения объёма желудка"},
        {"name": "Гастрошунтирование по Ру", "type": "bariatric", "description": "Комбинированная методика для стойкого снижения массы тела"},
        {"name": "Установка внутрижелудочного баллона", "type": "bariatric", "description": "Временная методика для коррекции веса"},
        {"name": "Холецистэктомия (удаление желчного пузыря)", "type": "general", "description": "Лапароскопическое удаление при желчнокаменной болезни"},
        {"name": "Грыжесечение (паховые, пупочные, вентральные)", "type": "general", "description": "Современные сетчатые импланты и надёжная фиксация"},
        {"name": "Аппендэктомия", "type": "general", "description": "Малоинвазивное удаление аппендикса"},
    ]


@app.get("/api/testimonials")
def get_testimonials(limit: int = 12):
    if db is None:
        return []
    try:
        items = get_documents("testimonial", limit=limit)
        return [
            {
                "name": i.get("name"),
                "procedure": i.get("procedure"),
                "rating": i.get("rating", 5),
                "text": i.get("text"),
                "city": i.get("city"),
            }
            for i in items
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/testimonials")
def create_testimonial(payload: Testimonial):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    try:
        _id = create_document("testimonial", payload)
        return {"id": _id, "ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/before-after")
def get_before_after(limit: int = 12):
    if db is None:
        return []
    try:
        items = get_documents("beforeafter", limit=limit)
        return [
            {
                "patient_code": i.get("patient_code"),
                "procedure": i.get("procedure"),
                "weight_before": i.get("weight_before"),
                "weight_after": i.get("weight_after"),
                "description": i.get("description"),
                "image_before_url": i.get("image_before_url"),
                "image_after_url": i.get("image_after_url"),
            }
            for i in items
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class BMIQuery(BaseModel):
    height_cm: float
    weight_kg: float


def _bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "Недостаточная масса"
    if bmi < 25:
        return "Норма"
    if bmi < 30:
        return "Избыточная масса"
    if bmi < 35:
        return "Ожирение I степени"
    if bmi < 40:
        return "Ожирение II степени"
    return "Ожирение III степени"


@app.post("/api/bmi")
def bmi_calc(data: BMIQuery):
    h_m = data.height_cm / 100.0
    if h_m <= 0:
        raise HTTPException(status_code=400, detail="Height must be greater than 0")
    bmi = data.weight_kg / (h_m * h_m)
    return {"bmi": round(bmi, 1), "category": _bmi_category(bmi)}


@app.post("/api/contact")
def send_contact(payload: ContactMessage):
    if db is None:
        # Allow site to work without DB, just accept
        return {"ok": True, "stored": False}
    try:
        _id = create_document("contactmessage", payload)
        return {"ok": True, "id": _id, "stored": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
            response["database_name"] = os.getenv("DATABASE_NAME") or "❌ Not Set"
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


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
