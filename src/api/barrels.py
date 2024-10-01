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
        barrel_green_ml =0

        gold_price = result.gold

        for barrel in barrels_delivered:
            barrel_green_ml += barrel.ml_per_barrel
            gold_price-= barrel.price

    
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = {barrel_green_ml}"))
    
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


        green_potions = result.num_green_potions
        gold_price = result.gold
        
        if  green_potions < 10:
                
            for barrel in wholesale_catalog:
                if barrel.price <= gold_price and barrel.sku == "SMALL_GREEN_BARREL":
                    gold_price-=barrel.price #reuce the amount of gold used to purchase
                    updated_barrel_qty +=1

            return [
                        {
                                    #"sku": "SMALL_RED_BARREL",
                            "sku" : "SMALL_GREEN_BARREL",
                            "quantity": updated_barrel_qty,  #update the barrel quantity
                        }
                    ]
                            
        #cannot afford
        return []

