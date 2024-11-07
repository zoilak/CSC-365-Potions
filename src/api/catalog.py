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
        result = connection.execute(sqlalchemy.text("""
                SELECT potion_types.sku, potion_types.cost, potion_types.red, 
                potion_types.green, potion_types.blue, potion_types.dark, 
                potion_types.name, COALESCE(SUM(potion_log.quantity),0) AS quantity
                FROM potion_log
                JOIN potion_types ON potion_log.pid = potion_types.id
                GROUP BY potion_types.id                                    
                 """)).fetchall()
        
        potions_on_catalog = 0

    for potion in result:
        potion_amount = potion.quantity

        if potion_amount!=0 and potions_on_catalog <6:
            catalog.append({
                "sku": potion.sku,
                "name": potion.name,
                "quantity": potion.quantity,
                "price": potion.cost,
                "potion_type": [potion.red_ml, potion.green_ml, potion.blue_ml, potion.dark_ml],
            })
            potions_on_catalog+=1

    #what exactly is in catalog
    for available in catalog:
            print(f"available potions: {available}")
    
    #else return empty
    return catalog
