from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse

app = FastAPI()

# Dummy IMSI-to-user_id mapping
IMSI_USER_MAP = {
    "714011002222222": "user_001",
    "714011002333333": "user_002",
    "714011002444444": "user_abc",
}

class ValidateRequest(BaseModel):
    imsi: str

@app.post("/validate")
async def validate_user(req: ValidateRequest):
    imsi = req.imsi
    if imsi in IMSI_USER_MAP:
        return {"status": "ok", "user_id": IMSI_USER_MAP[imsi]}
    return JSONResponse(status_code=403, content={"status": "error", "message": "Invalid IMSI"})
