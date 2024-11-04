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
        result_gold = connection.execute(sqlalchemy.text("SELECT COAELSCE(SUM(gold),0) as gold_amount FROM gold_tracker")).fetchone()
        result_potions = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(quantity),0)AS quant FROM potion_log")).fetchone()
        result_ml = connection.execute(sqlalchemy.text("""SELECT COALESCE(SUM(red),0) AS red_ml,
                                                       COALESCE(SUM(green),0)  AS green_ml,
                                                       COALESCE(SUM(blue),0) AS blue_ml,
                                                       COALESCE(SUM(dark),0) AS dark_ml
                                                       FROM barrel_ml_log""")).fetchone()

        
        total_ml = result_ml.red_ml + result_ml.green_ml + result_ml.blue_ml + result_ml.dark_ml
    
    return {"number_of_potions": result_potions.quant, "ml_in_barrels": total_ml, "gold": result_gold.gold_amount}

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
