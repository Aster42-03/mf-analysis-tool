from typing import List
from datetime import date

from sqlalchemy import Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class FundIndex(Base):
    __tablename__ = "fund_index"

    fund_house: Mapped[str] = mapped_column(nullable=False)
    scheme_type: Mapped[str] = mapped_column(nullable=False)
    scheme_category: Mapped[str] = mapped_column(nullable=False)
    scheme_code: Mapped[int] = mapped_column(nullable=False, primary_key=True)
    scheme_name: Mapped[str] = mapped_column(nullable=False)
    scheme_start_date: Mapped[date] = mapped_column(Date, nullable=False)

    nav: Mapped[List["HistoricalNav"]] = relationship(back_populates="fund")


class HistoricalNav(Base):
    __tablename__ = "historical_nav"

    scheme_code: Mapped[int] = mapped_column(
        ForeignKey("fund_index.scheme_code", ondelete="CASCADE"), primary_key=True
    )
    nav_date: Mapped[date] = mapped_column(Date, primary_key=True)
    nav: Mapped[float] = mapped_column(nullable=False)

    fund: Mapped["FundIndex"] = relationship(back_populates="nav")
