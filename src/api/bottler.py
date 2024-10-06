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
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).one()
        
        #green stuff
        total_green_ml = int(result.num_green_ml)
        total_green_potions = int(result.num_green_potions)

        #red stuff
        total_red_ml = int(result.num_red_ml)
        total_red_potions = int(result.num_red_potions)

        #blue stuff
        total_blue_ml = int(result.num_blue_ml)
        total_blue_potions = int(result.num_blue_potions)


        for potion in potions_delivered:
            
            if potion.potion_type == [0, 100, 0, 0]:
                total_green_potions += potion.quantity
                total_green_ml -= (potion.quantity * 100)

            elif potion.potion_type == [100, 0, 0, 0]:
                total_red_potions += potion.quantity
                total_red_ml -= (potion.quantity * 100)

            elif potion.potion_type == [0, 0, 100, 0]:
                total_blue_potions += potion.quantity
                total_blue_ml -= (potion.quantity * 100)

            # elif potion.potion_type == [0, 0, 0, 1]:
            #     total_green_potions += potion.quantity
            #     total_green_ml -= (potion.quantity * 100)

        # total_green_potions = total_green_ml // 100

        # total_green_ml -= total_green_potions * 100
        # print(f"delivering bottles green_ml: {total_green_ml}, green potions: {total_green_potions}")
        
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = {total_green_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = {total_green_potions}"))

        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {total_red_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = {total_red_potions}"))
        
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory" )).one()
        
        #amount per color potion
        new_green_ml = int(result.num_green_ml)
        new_red_ml = int(result.num_red_ml)
        new_blue_ml = int(result.num_blue_ml)

        #potion count
        green_potions_count = int(new_green_ml/100)
        red_potions_count = int(new_red_ml/100)
        blue_potions_count = int(new_blue_ml/100)

        #make all bottles into barrels
        # while num_green_ml >= 100:
        #     num_green_ml-=100
        #     connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = {num_green_ml}"))
        #     quantity_count += 1

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red/green potions.

    bottled_up =[]
    if red_potions_count >=0:
        bottled_up.append( [
                {
                    "potion_type": [100, 0, 0, 0],
                    "quantity": red_potions_count,
                }
            ])
        
    if green_potions_count >=0:
        bottled_up.append( [
                {
                    "potion_type": [0, 100, 0, 0],
                    "quantity": green_potions_count,
                }
            ])
        
    if blue_potions_count >=0:
        bottled_up.append( [
                {
                    "potion_type": [0, 0, 100, 0],
                    "quantity": blue_potions_count,
                }
            ])
        
    
    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = {green_potions_count}"))
    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = {red_potions_count}"))
    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_potions = {blue_potions_count}"))
        
    return bottled_up

if __name__ == "__main__":
    print(get_bottle_plan())