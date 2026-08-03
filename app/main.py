from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import schemas

from .dependencies import get_db
from .models import FundIndex, HistoricalNav


app = FastAPI()

db_dep = Annotated[ AsyncSession, Depends( get_db ) ]


@app.get( "/" )
async def root() -> Any:
    return { "message": "Hello" }


@app.get( "/fund/{code}", response_model = schemas.GetFund )
async def get_fund( code: int, db: db_dep ) -> Any:
    fund = await db.get( FundIndex, code, options = [ selectinload( FundIndex.nav ) ] )
    if not fund:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, detail = "Fund not Found"
        )
    return fund


@app.get( "/fund/nav/{code}", response_model = list[ schemas.GetNav ] )
async def get_nav( code: int, db: db_dep ) -> Any:
    res = select( HistoricalNav ).where( HistoricalNav.scheme_code == code )
    nav = await db.scalars( res )
    if not nav.all():
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, detail = "No Such Fund"
        )
    return nav.all()
