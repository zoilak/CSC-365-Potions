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
        result = connection.execute(sqlalchemy.text("SELECT num_green_potion FROM global_inventory"))

        for row in result:
            total_green_potions = row[0]

    if total_green_potions >=1:

        return [
                {
                    "sku": "GREEN_POTION_0",
                    "name": "green potion",
                    "quantity": total_green_potions,
                    "price": 50,
                    "potion_type": [0, 100, 0, 0],
                }
            ]
    
    #else return empty
    return []
