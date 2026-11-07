from fastapi import FastAPI, Query
from pydantic import BaseModel, HttpUrl

from contextlib import asynccontextmanager
from database import init_db, save_check, get_checks

from check import check_url


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Uptime Monitor", lifespan=lifespan)


class CheckRequest(BaseModel):
    url: HttpUrl


@app.post("/checks")
def create_check(request: CheckRequest):
    result = check_url(str(request.url))
    id = save_check(result=result)
    result["id"] = id

    return result

@app.get("/checks")
def get_check(limit: int = Query(default=20, ge=1, le=100)):
    return get_checks(limit=limit)


@app.get("/health")
def health():
    return {"status": "ok"}
