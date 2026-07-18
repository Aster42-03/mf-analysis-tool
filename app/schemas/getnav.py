from datetime import date
from pydantic import BaseModel, ConfigDict, Field



class GetNav(BaseModel):

    
    nav_date: date = Field(serialization_alias="Date")
    nav: float

    model_config = ConfigDict(from_attributes=True)
