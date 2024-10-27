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
        result_potions = connection.execute(sqlalchemy.text("""
                                                        SELECT *
                                                        FROM potion_storage
                                                        """
                                                    )).fetchall()     
        #getting the row_ml that is there and then subtracting this later

        total_red_ml = 0
        total_green_ml = 0
        total_blue_ml = 0
        total_dark_ml = 0


        potion_inventory = {}
        for row in result_potions:
            # potion_inventory[row.sku] = row.mls
            potion_inventory_type = tuple([row.red_ml, row.green_ml, row.blue_ml, row.dark_ml])
            #using potion_type as key
            potion_inventory[potion_inventory_type] = {
                'sku': row.sku,
                'quantity': row.quantity
            }

        for potion in potions_delivered:
            potion_list = potion.potion_type
                #check is that key exists, probably not the smartest thing to do but each potion type key is different
            potion_key = tuple(potion_list)
            if potion_key in potion_inventory:
                potion_stuff = potion_inventory[potion_key]
                potion_sku = potion_stuff['sku']
                potion_quantity = potion_stuff['quantity']

                actual_quantity= potion_quantity + potion.quantity
        

                connection.execute(sqlalchemy.text("""
                                UPDATE potion_storage 
                                SET quantity = :new_quantity 
                                WHERE sku = :sku
                        """), {"new_quantity": actual_quantity, "sku": potion_sku})
                
                #update ml_storage based in potions made
                total_red_ml += potion_list[0] * potion.quantity
                total_green_ml += potion_list[1] * potion.quantity
                total_blue_ml += potion_list[2] * potion.quantity
                total_dark_ml += potion_list[3] * potion.quantity
                
                connection.execute(sqlalchemy.text("""
                                        UPDATE ml_storage
                                        SET mls = CASE sku
                                            WHEN 'red' THEN mls - :red_ml
                                            WHEN 'green' THEN mls - :green_ml
                                            WHEN 'blue' THEN mls - :blue_ml
                                            WHEN 'dark' THEN mls - :dark_ml
                                            END
                                        WHERE sku IN ('red', 'green', 'blue', 'dark')
                                    """), {
                                        "red_ml": total_red_ml,
                                        "green_ml": total_green_ml,
                                        "blue_ml": total_blue_ml,
                                        "dark_ml": total_dark_ml
                                    })
                
            
            # else:
            #     print ("error: Inavlid potion type")
        
        return "OK"

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
            while potion.red_ml < ml_inventory['red'] and potion.blue_ml < ml_inventory['blue'] and potion.green_ml < ml_inventory['green'] and potion.dark_ml < ml_inventory['dark']:
                
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