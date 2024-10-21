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
        
        result_potion = connection.execute(sqlalchemy.text("""
                                                        SELECT *
                                                        FROM potion_storage
                                                        WHERE quantity < 5
                    
                                                        """
                                                    )).fetchall()
        #amount per color potion
        ml_inventory = {}
        for row in result:
            ml_inventory[row.sku] = row.mls
    
        
        bottled_up =[]

        for row in result_potion:
            # Create a potion_type based on the row values

            potion_type = [row.red_ml, row.green_ml, row.blue_ml, row.dark_ml]

            color_components = [('red', row.red_ml), ('green', row.green_ml), ('blue', row.blue_ml), ('dark', row.dark_ml)]

            # Initialize a list to hold the possible number of bottles for each color
            bottles_per_color = []

            # Calculate how many bottles can be made for each color that requires some amount of ml
            for color, potion_ml in color_components:
                if potion_ml > 0:
                    bottles_per_color.append(ml_inventory[color] // potion_ml)

            # Find the minimum number of bottles that can be made across all colors
        
            if bottles_per_color:
                min_bottles = min(bottles_per_color)  
            else :
                min_bottles = 0
            
            if min_bottles > 0:

                # Deduct the used ml from the ml_storage  
                for color, potion_ml in color_components:
                    if potion_ml > 0:  # Only deduct if we need that ml to make the potion
                        ml_inventory[color] -= min_bottles * potion_ml

                if row.red_ml > 0:
                    ml_inventory['red'] -= min_bottles * row.red_ml
                if row.green_ml > 0:
                    ml_inventory['green'] -= min_bottles * row.green_ml
                if row.blue_ml > 0:
                    ml_inventory['blue'] -= min_bottles * row.blue_ml
                if row.dark_ml > 0:
                    ml_inventory['dark'] -= min_bottles * row.dark_ml
            
            # Add the potion mixture details dynamically
                bottled_up.append({
                    "potion_type": potion_type,
                    "quantity": min_bottles
                })
   
        
    print("get_bottle_plan:", bottled_up)  
    return bottled_up

if __name__ == "__main__":
    print(get_bottle_plan())