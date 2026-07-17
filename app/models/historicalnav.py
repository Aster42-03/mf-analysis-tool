from datetime import date

from sqlalchemy import Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class HistoricalNav(Base):
    __tablename__ = "historical_nav"

    scheme_code: Mapped[int] = mapped_column(
        ForeignKey("fund_index.scheme_code", ondelete="CASCADE"), primary_key=True
    )
    nav_date: Mapped[date] = mapped_column(Date, primary_key=True)
    nav: Mapped[float] = mapped_column(nullable=False)

    fund: Mapped["FundIndex"] = relationship(back_populates="nav")
