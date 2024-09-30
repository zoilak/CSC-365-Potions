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
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory" ))

        for row in result:
            gold_price = row[2]

            for barrel in barrels_delivered:
                barrel_green_ml += barrel.ml_per_barrel
                gold_price-= barrel.price
    
    #upadte green_ml
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = barrel_green_ml" ))

    #update gold
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold_price" ))

    return "OK"

# Gets called once a day
# purchase a new small green/red potion barrel only if the number of potions in inventory is less than 10
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory" ))

        for row in result:
            num_green_potions = row[0]
            gold_price = row[2]
            if  num_green_potions < 10:
                updated_barrel_qty = 0

                for barrel in wholesale_catalog:
                    if barrel.price <= gold and barrel.sku == "SMALL_GREEN_BARREL":
                        gold_price-=barrel.price #reuce the amount of gold used to purchase
                        updated_barrel_qty +=1
                        
                return [
                            {
                                #"sku": "SMALL_RED_BARREL",
                                "sku" : barrel.sku
                                "quantity": updated_barrel_qty,  #update the barrel quantity
                            }
                        ]
                        
            else:
                #cannot afford
                return []

