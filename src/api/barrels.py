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

        gold_price = 0
        barrel_blue_ml = 0
        barrel_red_ml = 0
        barrel_green_ml =0
        barrel_dark_ml =0
        for barrel in barrels_delivered:
            gold_price -= (barrel.price * barrel.quantity)
            if "green" in barrel.sku:
                
                barrel_green_ml += barrel.ml_per_barrel * barrel.quantity
                
                
            elif "red" in barrel.sku:
                # red_barrels += barrel.quantity
                barrel_red_ml += barrel.ml_per_barrel * barrel.quantity
                
            elif "blue" in barrel.sku:
                barrel_blue_ml += barrel.ml_per_barrel * barrel.quantity
            

            elif "dark" in barrel.sku:
                barrel_dark_ml += barrel.ml_per_barrel * barrel.quantity
            
        
        #update ml
        connection.execute(sqlalchemy.text("""
                                                UPDATE ml_storage SET mls = :green_ml WHERE sku = 'green';
                                                UPDATE ml_storage SET mls = :red_ml WHERE sku = 'red';
                                                UPDATE ml_storage SET mls = :blue_ml WHERE sku = 'blue';
                                                UPDATE ml_storage SET mls = :dark_ml WHERE sku = 'dark';
                                            """), {
                                                "green_ml": barrel_green_ml,
                                                "red_ml": barrel_red_ml,
                                                "blue_ml": barrel_blue_ml,
                                                "dark_ml": barrel_dark_ml
                                            })

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

        max_barrels = 0

        updated_barrel_qty = 0
        barrels_to_purchase = []
        local_barrels = {
            'red': [1,0,0,0],
            'green': [0,1,0,0],
            'blue': [0,0,1,0],
            'dark': [0,0,0,1]
        }
        

        #barrels being sold        
        for barrel in wholesale_catalog:
            updated_barrel_qty = 0
            #the max amount of barrels i can purchase from that barrel in catalog with the money i have
            if barrel.price > 0:
                max_barrels = gold_amount//barrel.price

            #procees only if you have enoough to buy at least 1 barrel
            if max_barrels > 0:
                
                #check current inventory
                for row in result_barrel:
                    if local_barrels[row.sku] == barrel.potion_type and row.mls < 100:
                        updated_barrel_qty += 1
                        barrels_to_purchase.append(
                                {
                                            
                                    "sku" : barrel.sku,
                                    "quantity": updated_barrel_qty,  #update the barrel quantity
                                }
                        )


                    gold_amount-= barrel.price * updated_barrel_qty
                    
                    #row["quantity"] = max_barrels
                    #update price of barrels purchased
                    

            else:
                print(f"Can't afford barrel ${barrel.sku}")
        
        for purchased in barrels_to_purchase:
            print(f"barrels purchasing: {purchased}")

        return barrels_to_purchase

#certain problems in code I don't think i am currently maximizing
#the exact amount of barrels to buy :(