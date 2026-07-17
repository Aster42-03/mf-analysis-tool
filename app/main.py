from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app import models
from .depenencies import get_db
from .database import engine

app = FastAPI()

models.Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "hello"}


@app.get("/test")
def db_test(db: Session = Depends(get_db)):
    return {"status": "success"}
