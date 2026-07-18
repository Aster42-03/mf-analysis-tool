from typing import Annotated
from fastapi import FastAPI, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from .depenencies import get_db
from .database import engine, Base
from .models import FundIndex, HistoricalNav
from app import schemas

app = FastAPI()

Base.metadata.create_all(bind=engine)

db_dep = Annotated[Session, Depends(get_db)]


@app.get("/")
def root():
    return {"message": "hello"}


@app.get("/fund/{code}", response_model=schemas.GetFund)
def get_fund(code: int, db: db_dep):
    fund = db.get(FundIndex, str(code))
    return fund


@app.get("/fund/nav/{code}", response_model=list[schemas.GetNav])
def get_nav(code: int, db: db_dep):

    res = db.execute(select(HistoricalNav).where(HistoricalNav.scheme_code == code))
    nav = res.scalars().all()
    return nav
