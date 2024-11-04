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
        for potion in potions_delivered:

            print(f"Inserting ml into barrel_ml_log: red={-potion.potion_type[0] * potion.quantity}, green={-potion.potion_type[1] * potion.quantity}, 
                  blue={-potion.potion_type[2] * potion.quantity}, dark={-potion.potion_type[3] * potion.quantity}")
            print(f"Inserting potion into potion_log: pID={potion.potion_type}, quantity={potion.quantity}")

            # Insert into barrel_ml_log for ml usage
            connection.execute(sqlalchemy.text("""
                INSERT INTO barrel_ml_log (red, green, blue, dark)
                VALUES (:barrel_red_ml, :barrel_green_ml, :barrel_blue_ml, :barrel_dark_ml)
            """), {
                "barrel_red_ml": -potion.potion_type[0] * potion.quantity,
                "barrel_green_ml": -potion.potion_type[1] * potion.quantity,
                "barrel_blue_ml": -potion.potion_type[2] * potion.quantity,
                "barrel_dark_ml": -potion.potion_type[3] * potion.quantity
            })

            # Insert into potion_log to track potion delivery
            connection.execute(sqlalchemy.text("""
                INSERT INTO potion_log (pID, quantity)
                VALUES (
                    (SELECT ID FROM potion_types WHERE red_ml = :red_ml AND green_ml = :green_ml 
                    AND blue_ml = :blue_ml AND dark_ml = :dark_ml), 
                    :quantity
                )
            """), {
                "quantity": potion.quantity,
                "red_ml": potion.potion_type[0],
                "green_ml": potion.potion_type[1],
                "blue_ml": potion.potion_type[2],
                "dark_ml": potion.potion_type[3]
            })

print("OK")


@router.post("/plan")


#yellow = red and green
#violet = red and blue
#cyan = green and blue
#     = 
def get_bottle_plan():
    """
    Go from barrel to bottle. Max 100 ml each bottle, can mix up
    """

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""
                                                        SELECT sku, mls, quantity
                                                        FROM ml_storage
                                                        WHERE sku IN ('red', 'blue', 'green', 'dark')
                                                        """
                                                    )).fetchall()
        
        #only make potions for those that have less than 5 potion of potions in their storage
        result_potion = connection.execute(sqlalchemy.text("""
                                                        SELECT *
                                                        FROM potion_storage
                                                        WHERE quantity < 5
                    
                                                        """
                                                    )).fetchall()
       
       #returns a dictionary with color as key and ml as quantity
        ml_inventory = {}
        for row in result:
            ml_inventory[row.sku] = row.mls
    
        potions_made = 0
        bottled_up =[]


        #decided to use a simpler logic/ might go back to my previous bottling logic
        #for row (potion) from db
        for potion in result_potion:
           #how much ml is needed to make that potion
            potion_type =  [potion.red_ml, potion.green_ml, potion.blue_ml, potion.dark_ml]

            #check if i have enough to make that potion
            while (potion.red_ml < ml_inventory['red'] and 
                   potion.blue_ml < ml_inventory['blue'] and 
                   potion.green_ml < ml_inventory['green'] and 
                   potion.dark_ml < ml_inventory['dark']):
                
                potions_made +=1

                ml_inventory["red"] -= potion.red_ml
                ml_inventory["blue"] -= potion.blue_ml
                ml_inventory["dark"] -= potion.dark_ml
                ml_inventory["green"] -= potion.green_ml
            
            
            if potions_made > 0:    
                bottled_up.append({
                            "potion_type": potion_type,
                            "quantity": potions_made
                            })

            potions_made =0

    print(bottled_up)
    return bottled_up

if __name__ == "__main__":
    print(get_bottle_plan())