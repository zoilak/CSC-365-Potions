from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    catalog=[]
    
    with db.engine.begin() as connection:
        # get all of the potions that are not 0
        result = connection.execute(sqlalchemy.text("SELECT * FROM potion_storage WHERE quantity != 0")).fetchall()
        
    for potion in result:
        catalog.append({
            "sku": potion.sku,
            "name": potion.sku,
            "quantity": potion.quantity,
            "price": potion.cost,
            "potion_type": [potion.red_ml, potion.green_ml, potion.blue_ml, potion.dark_ml],
        })
    
    #else return empty
    return catalog
