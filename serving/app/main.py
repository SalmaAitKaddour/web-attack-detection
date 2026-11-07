from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Web Attack Detection API")

class Request(BaseModel):
    text: str  # requête normalisée (method + path + params + body)

@app.post("/predict")
def predict(req: Request):
    # TODO : charger le meilleur modèle + prétraitement
    return {"label": 0, "score": 0.0}
