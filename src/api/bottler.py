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
        result_ml = connection.execute(sqlalchemy.text("""
                        SELECT 
                        COAELSCE(SUM(red),0) AS red_ml,
                        COAELSCE(SUM(blue),0) AS blue_ml,
                        COAELSCE(SUM(green),0) AS green_ml,
                        COAELSCE(SUME(dark),0) AS dark_ml                                                                                       
                        FROM barrel_ml_log       
                        """
                        )).fetchone()
        
        #only make potions for those that have less than 5 potion of potions in their storage
        result_potion = connection.execute(sqlalchemy.text("""
                        SELECT potion_types.sku, potion_types.cost, potion_types.red, 
                        potion_types.green, potion_types.blue, potion_types.dark, 
                        potion_types.name, COALESCE(SUM(potion_log.quantity),0) AS quantity
                        FROM potion_log
                        JOIN potion_types ON potion_log.pID = potion_types.id
                        GROUP BY potion_types.id """
                        )).fetchall()
       
       #returns a dictionary with color as key and ml as quantity

        ml_inventory = {
           "red_cur_ml": result_ml.red_ml,
           "blue_cur_ml": result_ml.blue_ml,
           "green_cur_ml": result_ml.green_ml,
           "dark_cur_ml" : result_ml.dark_ml
        }
      
    
        potions_made = 0
        bottled_up =[]


        #decided to use a simpler logic/ might go back to my previous bottling logic
        #for row (potion) from db
        for row in result_potion:
            sku = row.sku
            cost = row.cost
            red = row.red
            green = row.green
            blue = row.blue
            dark = row.dark
            name = row.name
            quantity = row.quantity
            
            #if that potion count is 0
            if (quantity == 0):
           
                potion_mix =  [red, green, blue, dark]

                #check if i have enough to make that potion
                while (red< ml_inventory['red'] and 
                    blue< ml_inventory['blue'] and 
                    green< ml_inventory['green'] and 
                    dark< ml_inventory['dark']):
                    
                    potions_made +=1

                    ml_inventory["red"] -= red
                    ml_inventory["blue"] -= blue
                    ml_inventory["dark"] -= dark
                    ml_inventory["green"] -= green
                
                
                if potions_made > 0:    
                    bottled_up.append({
                                "potion_type": potion_mix,
                                "quantity": potions_made
                                })

            potions_made =0

    print(bottled_up)
    return bottled_up

if __name__ == "__main__":
    print(get_bottle_plan())