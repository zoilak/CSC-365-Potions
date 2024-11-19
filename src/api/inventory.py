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
        result_gold = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(gold),0) as gold_amount FROM gold_tracker")).fetchone()
        result_potions = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(quantity),0)AS quant FROM potion_log")).fetchone()
        result_ml = connection.execute(sqlalchemy.text("""SELECT COALESCE(SUM(red),0) AS red_ml,
                                                       COALESCE(SUM(green),0)  AS green_ml,
                                                       COALESCE(SUM(blue),0) AS blue_ml,
                                                       COALESCE(SUM(dark),0) AS dark_ml
                                                       FROM barrel_ml_log""")).fetchone()

        
        total_ml = result_ml.red_ml + result_ml.green_ml + result_ml.blue_ml + result_ml.dark_ml

        result_potion_types = connection.execute(sqlalchemy.text("""SELECT pid, (SUM(quantity)) AS 
                                                                 quantity FROM potion_log GROUP BY pid""")).fetchall()

        print("Detailed Potion Inventory:")
        for potion in result_potion_types:
            print(f"Potion ID: {potion.pid}, Quantity: {potion.quantity}")

      
    
    return {"number_of_potions": result_potions.quant, "ml_in_barrels": total_ml, "gold": result_gold.gold_amount}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    cur_inventory = get_inventory()
    cur_gold = cur_inventory["gold"]
    
    potion_capacity = 0
    ml_capacity = 0

    # potion_threshold = float(cur_potions) * float(potion_cap) * 0.2
    # ml_threshold = float(cur_ml) * float(ml_cap) * 0.2
    # gold_check = float(cur_gold) * float(cost_cap) * 0.2

    #if potion_capacity reaches threshold, increase it by 1
    if (cur_gold > 1000) :
        potion_capacity += 1

    #if ml_capacity reaches threshold increas it by 1
    if (cur_gold > 1000) :
        ml_capacity += 1
    
    return {
        "potion_capacity": potion_capacity,
        "ml_capacity": ml_capacity
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
    cost = 1000

    with db.engine.begin() as connection:
        
        result_gold = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(gold),0) as gold_amount FROM gold_tracker")).scalar()
       
        if (result_gold >10000):
            
            if (capacity_purchase.potion_capacity!=0):
                connection.execute(sqlalchemy.text(""" 
                                                            INSERT INTO gold_tracker (gold)
                                                            VALUES (:gold)
                                                        """), {"gold": -cost})
                
                connection.execute(sqlalchemy.text(
                    "UPDATE capacity_plan SET potion_capacity = potion_capacity + :potion_capacity"),
                    {"potion_capacity": capacity_purchase.potion_capacity})
                        
            if (capacity_purchase.ml_capacity !=0):
            
            # Deduct the gold from the gold tracker
                connection.execute(sqlalchemy.text(""" 
                                                            INSERT INTO gold_tracker (gold)
                                                            VALUES (:gold)
                                                        """), {"gold": -cost})
                

                # Increase potion and ml capacities
                connection.execute(sqlalchemy.text(
                    "UPDATE capacity_plan SET ml_capacity = ml_capacity + :ml_capacity"),
                    {"ml_capacity": capacity_purchase.ml_capacity})
                
    return "OK"
