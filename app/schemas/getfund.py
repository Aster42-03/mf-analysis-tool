from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class GetFund(BaseModel):
    fund_house: str = Field(serialization_alias="House")
    scheme_type: str = Field(serialization_alias="Type")
    scheme_category: str = Field(serialization_alias="Category")
    scheme_code: int = Field(serialization_alias="Code")
    scheme_name: str = Field(serialization_alias="Name")
    scheme_start_date: date = Field(serialization_alias="Start Date")

    model_config = ConfigDict(from_attributes=True)
