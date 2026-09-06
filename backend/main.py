from fastapi import FastAPI

app = FastAPI(title="Sistema de Gestión Farmacia - API")


@app.get("/")
def status():
    return {"status": "ok", "mensaje": "Backend funcionando"}
