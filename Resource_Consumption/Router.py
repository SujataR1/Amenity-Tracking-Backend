from fastapi import APIRouter

# Import the individual routers
from .Electricity_Consumption_Router import (
    Electricity_Consumption_Router,
)
from .Gas_Consumption_Router import Gas_Consumption_Router
from .Water_Consumption_Router import Water_Consumption_Router
from .Fuel_Consumption_Router import Fuel_Consumption_Router

# Create a parent router for all consumption-related routers
Consumption_Router = APIRouter()

routers = [
    {
        "router": Electricity_Consumption_Router,
        "prefix": "/electricity",
        "tags": ["Electricity Consumption"],
    },
    {
        "router": Gas_Consumption_Router,
        "prefix": "/gas",
        "tags": ["Gas Consumption"],
    },
    {
        "router": Water_Consumption_Router,
        "prefix": "/water",
        "tags": ["Water Consumption"],
    },
    {
        "router": Fuel_Consumption_Router,
        "prefix": "/fuel",
        "tags": ["Fuel Consumption"],
    },
]

for route in routers:
    Consumption_Router.include_router(
        route["router"], prefix=route["prefix"], tags=route["tags"]
    )
