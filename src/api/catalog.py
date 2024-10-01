from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).one()

        
        total_green_potions = result.num_green_potions

    if total_green_potions >=1:

        return [
                {
                    "sku": "GREEN_POTION_0",
                    "name": "green potion",
                    "quantity": total_green_potions,
                    "price": 30,    #lower price so they sell
                    "potion_type": [0, 100, 0, 0],
                }
            ]
    
    #else return empty
    return []
