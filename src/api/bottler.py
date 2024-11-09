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
            print("potion_type contents:", potion.potion_type)  # This will print the contents of potion_type
            print("potion quantity:", potion.quantity)

            # Insert into barrel_ml_log for ml usage
            connection.execute(sqlalchemy.text("""
                INSERT INTO barrel_ml_log (red, green, blue, dark)
                VALUES (:red_ml, :green_ml, :blue_ml, :dark_ml)
            """), [{
                "red_ml": -potion.potion_type[0] * potion.quantity,
                "green_ml": -potion.potion_type[1] * potion.quantity,
                "blue_ml": -potion.potion_type[2] * potion.quantity,
                "dark_ml": -potion.potion_type[3] * potion.quantity
            }])

            # Insert into potion_log to track potion delivery
            connection.execute(sqlalchemy.text("""
                INSERT INTO potion_log (pid, quantity)
                VALUES (
                    (SELECT id FROM potion_types WHERE red_ml = :red_ml AND green_ml = :green_ml 
                    AND blue_ml = :blue_ml AND dark_ml = :dark_ml), :quantity)"""), [{
                "quantity": potion.quantity,
                "red_ml": potion.potion_type[0],
                "green_ml": potion.potion_type[1],
                "blue_ml": potion.potion_type[2],
                "dark_ml": potion.potion_type[3]
            }])

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
                        COALESCE(SUM(red),0) AS red_ml,
                        COALESCE(SUM(blue),0) AS blue_ml,
                        COALESCE(SUM(green),0) AS green_ml,
                        COALESCE(SUM(dark),0) AS dark_ml                                                                                      
                        FROM barrel_ml_log;      
                        """
                        )).fetchone()
        
     
        result_potion = connection.execute(sqlalchemy.text("""
                    SELECT 
                        potion_types.sku, 
                        potion_types.cost, 
                        potion_types.red_ml, 
                        potion_types.green_ml, 
                        potion_types.blue_ml, 
                        potion_types.dark_ml, 
                        potion_types.name, 
                        COALESCE(SUM(potion_log.quantity), 0) AS quantity
                    FROM potion_log
                    RIGHT JOIN potion_types ON potion_log.pid = potion_types.id
                    GROUP BY 
                        potion_types.sku, 
                        potion_types.cost, 
                        potion_types.red_ml, 
                        potion_types.green_ml, 
                        potion_types.blue_ml, 
                        potion_types.dark_ml, 
                        potion_types.name
                    ORDER BY random();"""
                        )).fetchall()
       
       #returns a dictionary with color as key and ml as quantity

        ml_inventory = {
           "red": result_ml.red_ml,
           "blue": result_ml.blue_ml,
           "green": result_ml.green_ml,
           "dark" : result_ml.dark_ml
        }
      
    
        
        bottled_up =[]

        #make indivdual potion capacity limits, look at how many i currently have and dont bottle over

        #add a boolean logic to only bottle certain potions

        #decided to use a simpler logic/ might go back to my previous bottling logic
        #for row (potion) from db
        #put a while loop over all of it to add one potion at a time, fill all of them evenly'
        potion_made = True
        while potion_made:
            potion_made = False
            for row in result_potion:
                sku = row.sku
                cost = row.cost
                red = row.red_ml
                green = row.green_ml
                blue = row.blue_ml
                dark = row.dark_ml
                name = row.name
                quantity = row.quantity
                
                #if that potion count is 0
                if (quantity < 100):
            
                    potion_mix =  [red, green, blue, dark]

                    #check if i have enough to make that potion
                    if (red<= ml_inventory['red'] and blue<= ml_inventory['blue'] and green<=ml_inventory['green'] and dark<= ml_inventory['dark']):

                        #put number of capcity here
                        max_potions_possible = min(
                            (ml_inventory["red"] // red) if red > 0 else float('inf'),
                            (ml_inventory["green"] // green) if green > 0 else float('inf'),
                            (ml_inventory["blue"] // blue) if blue > 0 else float('inf'),
                            (ml_inventory["dark"] // dark) if dark > 0 else float('inf'),
                        )

                        
                        if max_potions_possible > 0:
                            # Update ml inventory
                            ml_inventory["red"] -= red * max_potions_possible
                            ml_inventory["green"] -= green * max_potions_possible
                            ml_inventory["blue"] -= blue * max_potions_possible
                            ml_inventory["dark"] -= dark * max_potions_possible

                            bottled_up.append({
                                "potion_type": potion_mix,
                                "quantity": max_potions_possible
                            })
                            print(f"Just made potion {name}. Remaining ml: red={ml_inventory['red']}, green={ml_inventory['green']}, blue={ml_inventory['blue']}, dark={ml_inventory['dark']}")

                    else:
                        print(f"Not enough ml for {name}. Required: red={red}, green={green}, blue={blue}, dark={dark}")


    print(bottled_up)
    return bottled_up

if __name__ == "__main__":
    print(get_bottle_plan())