from fastapi import FastAPI, HTTPException
from sqlalchemy.exc import OperationalError
from sqlmodel import text

from .api.blogs import blogs_router
from .api.users import users_router
from .db import SessionDep

app = FastAPI()


@app.get("/")
def get_health():
    return {"message": "TechBlog API"}


@app.get("/health/db")
def get_db_health(
    session: SessionDep,
):
    try:
        result = session.exec(text("SELECT 1"))
        return {"database": "connected", "result": result.scalar()}
    except OperationalError as _:
        raise HTTPException(status_code=503, detail="database connection failed")


app.include_router(users_router)
app.include_router(blogs_router)
