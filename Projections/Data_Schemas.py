from pydantic import BaseModel
from Machine_Learning.Data_Schemas import ResourceTypeEnum


class ProjectionRequest(BaseModel):
    resource_type: ResourceTypeEnum
    month: str  # Month name (e.g., "January", "February")
    year: int  # Year (e.g., 2024)
