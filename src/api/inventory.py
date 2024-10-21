from fastapi import APIRouter, Depends
from pydantic import BaseModel
import pydantic
from src.api import auth
import math
import sqlalchemy
from src import database as db


router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """ call all potions, call gold, call ml"""
    with db.engine.begin() as connection:
        # result_ml = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory" )).fetchall()
        result_gold = connection.execute(sqlalchemy.text("SELECT gold FROM gold_tracker")).one()
        result_potions = connection.execute(sqlalchemy.text("SELECT quantity FROM potion_storage")).fetchall()

        for quant in result_potions:
            total_potions+= quant.quantity
        
        # total_ml = int(result.num_green_ml) + int(result.num_red_ml) + int(result.num_blue_ml)
        
        total_gold = result_gold.gold
        total_ml = 0

    
    return {"number_of_potions": total_potions, "ml_in_barrels": total_ml, "gold": total_gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return {
        "potion_capacity": 0,
        "ml_capacity": 0
        }

class CapacityPurchase(pydantic.BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return "OK"
