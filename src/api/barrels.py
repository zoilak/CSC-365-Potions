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

    barrel_green_ml = 0
    barrel_blue_ml =0   
    barrel_red_ml =0
    barrel_dark_ml =0
    gold_price = 0

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

    print("red barrels delivered: ",barrel_green_ml )
    print("green barrels delivered: ",barrel_red_ml )
    print("blue barrels delivered: ",barrel_blue_ml )
    print("dark barrels delivered: ",barrel_dark_ml )

    with db.engine.begin() as connection:
        
        #update ml
        connection.execute(sqlalchemy.text("UPDATE ml_storage SET quantity = :green_ml WHERE sku = 'green'"), {"green_ml": barrel_green_ml})
        connection.execute(sqlalchemy.text( "UPDATE ml_storage SET quantity = :red_ml WHERE sku = 'red'"), {"red_ml": barrel_red_ml})
        connection.execute(sqlalchemy.text("UPDATE ml_storage SET quantity = :blue_ml WHERE sku = 'blue'"), {"blue_ml": barrel_blue_ml})
        connection.execute(sqlalchemy.text("UPDATE ml_storage SET quantity = :dark_ml WHERE sku = 'dark'" ), {"dark_ml": barrel_dark_ml})

        #update gold
        connection.execute(sqlalchemy.text("UPDATE gold_tracker SET gold = :gold_cur" ), {"gold_cur": gold_price})
    

    return "OK"

# Gets called once a day

@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        result_barrel = connection.execute(sqlalchemy.text("""
                                                        SELECT sku, mls, quantity
                                                        FROM ml_storage
                                                        WHERE sku IN ('red', 'blue', 'green', 'dark')
                                                        """
                                                    )).fetchall()
        
        result_gold = connection.execute(sqlalchemy.text("SELECT gold FROM gold_tracker")).one()
        
        gold_amount = result_gold.gold

        updated_barrel_qty = 0
        barrels_to_purchase = []

        #barrels being sold        
        for barrel in wholesale_catalog:
            
            #the max amount of barrels i can purchase from that barrel in catalog with the money i have
            max_barrels = gold_amount//barrel.price

            #procees only if you have enoough to buy at least 1 barrel
            if max_barrels > 0:
                
                #check current inventory
                for row in result_barrel:

                    if row['sku'] == barrel.sku and row['mls'] < 100 and row ['quantity'] > 0:
                        updated_barrel_qty += 1
                        barrels_to_purchase.append(
                                {
                                            
                                    "sku" : barrel.sku,
                                    "quantity": updated_barrel_qty,  #update the barrel quantity
                                }
                    )
                    
                    updated_barrel_qty = 0
                    #row["quantity"] = max_barrels
                    #update price of barrels purchased
                    gold_amount-= barrel.price * max_barrels

            else:
                print("Error buying barrels")
        for purchased in barrels_to_purchase:
            print(f"barrels purchasing: {purchased}")

        return barrels_to_purchase

#certain problems in code I don't think i am currently maximizing
#the exact amount of barrels to buy :(