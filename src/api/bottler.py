from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth

import sqlalchemy
from src import database as db


router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_ml, num_green_potions FROM global_inventory")).one()
        
        total_green_ml = result.num_green_ml
        total_green_potions = result.num_green_potions

        for potion in potions_delivered:
            if potion.potion_type == [0, 1, 0, 0]:
                total_green_potions += potion.quantity
                total_green_ml -= (potion.quantity * 100)

        # total_green_potions = total_green_ml // 100

        # total_green_ml -= total_green_potions * 100
        print(f"delivering bottles green_ml: {total_green_ml}, green potions: {total_green_potions}")
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = {total_green_ml}"))

    
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = {total_green_potions}"))
        
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_ml, num_green_potions FROM global_inventory" )).one()
        
        num_green_ml = result.num_green_ml
        quantity_count = 0


        #make all bottles into barrels
        while num_green_ml >= 100:
            num_green_ml-=100
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = {}".format(num_green_ml)))
            quantity_count += 1

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red/green potions.

    return [
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": quantity_count,
            }
        ]

if __name__ == "__main__":
    print(get_bottle_plan())