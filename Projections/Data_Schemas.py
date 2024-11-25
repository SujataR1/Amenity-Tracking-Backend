from pydantic import BaseModel


class ProjectionRequest(BaseModel):
    user_id: str
    month: str  # Month name (e.g., "January", "February")
    year: int  # Year (e.g., 2024)
