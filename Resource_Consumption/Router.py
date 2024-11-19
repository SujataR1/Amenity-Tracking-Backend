from fastapi import APIRouter

# Import the individual routers
from .Electricity_Consumption_Router import Electricity_Consumption_Router
from .Gas_Consumption_Router import Gas_Consumption_Router
from .Water_Consumption_Router import Water_Consumption_Router
from .Fuel_Consumption_Router import Fuel_Consumption_Router

# Create a parent router for all consumption-related routers
Consumption_Router = APIRouter()

# Include the individual routers into the parent router
Consumption_Router.include_router(
    Electricity_Consumption_Router,
    prefix="/electricity",
    tags=["Electricity Consumption"],
)
Consumption_Router.include_router(
    Gas_Consumption_Router, prefix="/gas", tags=["Gas Consumption"]
)
Consumption_Router.include_router(
    Water_Consumption_Router, prefix="/water", tags=["Water Consumption"]
)
Consumption_Router.include_router(
    Fuel_Consumption_Router, prefix="/fuel", tags=["Fuel Consumption"]
)
