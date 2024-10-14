from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db


router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory" )).one()
       

        #maybe chekc eahc barrel and update its ml in inventory
        barrel_green_ml = 0
        barrel_blue_ml =0   
        barrel_red_ml =0
        barrel_dark_ml =0

        barrel_ml = 0
        
        gold_price = int(result.gold)

        for barrel in barrels_delivered:
            if "green" in barrel.sku:
                barrel_green_ml += barrel.ml_per_barrel * barrel.quantity
                gold_price-= barrel.price
            
            elif "red" in barrel.sku:
                barrel_blue_ml += barrel.ml_per_barrel * barrel.quantity
                gold_price-= barrel.price
            
            elif "blue" in barrel.sku:
                barrel_blue_ml += barrel.ml_per_barrel * barrel.quantity
                gold_price-= barrel.price

            elif "dark" in barrel.sku:
                barrel_dark_ml += barrel.ml_per_barrel * barrel.quantity
                gold_price -= barrel.price

    
        #total ml
        barrel_ml = barrel_red_ml + barrel_blue_ml + barrel_green_ml

        print("total ml", barrel_ml)
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = {barrel_green_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {barrel_red_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = {barrel_blue_ml}"))

        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {gold_price}"))

    return "OK"

# Gets called once a day
# purchase a new small green/red potion barrel only if the number of potions in inventory is less than 10
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory" )).one()
        updated_barrel_qty = 0

        #quantity of barrels to buy
        small = "small"
        mini = "mini"
        large = "large"


        green_potions = int(result.num_green_potions)
        red_potions = int(result.num_red_potions)
        blue_potions = int(result.num_blue_potions)


        gold_price = int(result.gold)
        barrels_to_purchase = []

        #only buy barrel for potions which has the least inventory
        if green_potions < red_potions and green_potions < blue_potions:
            least_potions = "green"

        elif red_potions < blue_potions and red_potions < green_potions:
            least_potions = "red"

        else:
            least_potions = "blue"
                
        for barrel in wholesale_catalog:
            #check if you have enough money to buy a large barrel first
            if barrel.price <= gold_price and large in barrel.sku.lower():
                
                if least_potions in barrel.sku.lower():
                    gold_price-=barrel.price #reuce the amount of gold used to purchase
                    updated_barrel_qty +=1
                    
                    barrels_to_purchase.append(
                                {
                                                
                                    "sku" : barrel.sku,
                                    "quantity": updated_barrel_qty,  #update the barrel quantity
                                }
                    )
            
            if barrel.price <= gold_price and small in barrel.sku.lower(): 
                if least_potions in barrel.sku.lower():
                    gold_price-=barrel.price 
                    updated_barrel_qty +=1
                    
                    barrels_to_purchase.append(
                                {
                                            
                                    "sku" : barrel.sku,
                                    "quantity": updated_barrel_qty,  #update the barrel quantity
                                }
                    )

            # if barrel.price <= gold_price and mini in barrel.sku.lower(): #CHNAGED LOGIC TO TRY BUYING A MINI BARREL FIRST
            #     if least_potions in barrel.sku.lower():
            #         gold_price-=barrel.price 
            #         updated_barrel_qty +=1
                    
            #         barrels_to_purchase.append(
            #                     {
                                                
            #                         "sku" : barrel.sku,
            #                         "quantity": updated_barrel_qty,  #update the barrel quantity
            #                     }
            #         )
                        
        #barrels that have been purchased
        for purchased in barrels_to_purchase:
            print(f"barrels purchasing: {purchased}")

        return barrels_to_purchase

