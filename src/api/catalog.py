from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    empty_catalog=[]

    #need tp add all potions now
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions, num_blue_potions, num_red_potions FROM global_inventory")).one()
        
        total_green_potions = int(result.num_green_potions)
        total_red_potions = result.num_red_potions
        total_blue_potions = result.num_blue_potions

    if total_green_potions > 0:
         return [
                {
                    "sku": "GREEN_POTION_0",
                    "name": "green potion",
                    "quantity": total_green_potions,
                    "price": 60,    
                    "potion_type": [0, 100, 0, 0],
                }
            ]
    
    if total_blue_potions >=1:
        return [
                    {
                        "sku": "BLUE_POTION_0",
                        "name": "blue potion",
                        "quantity": total_blue_potions,
                        "price": 60,    #lower price so they sell
                        "potion_type": [100, 0, 0, 0],
                    }
                ]
    
    if total_red_potions >=1:
        return [
                    {
                        "sku": "RED_POTION_0",
                        "name": "red potion",
                        "quantity": total_red_potions,
                        "price": 60,    #lower price so they sell
                        "potion_type": [0, 0, 100, 0],
                    }
                ]
    

        
    #else return empty
    return empty_catalog
