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
                SELECT 
                        potion_types.sku, 
                        potion_types.cost, 
                        potion_types.red_ml, 
                        potion_types.green_ml, 
                        potion_types.blue_ml, 
                        potion_types.dark_ml, 
                        potion_types.name, 
                        COALESCE(SUM(potion_log.quantity), 0) AS quantity
                    FROM potion_log
                    RIGHT JOIN potion_types ON potion_log.pid = potion_types.id
                    GROUP BY 
                        potion_types.sku, 
                        potion_types.cost, 
                        potion_types.red_ml, 
                        potion_types.green_ml, 
                        potion_types.blue_ml, 
                        potion_types.dark_ml, 
                        potion_types.name                                   
                 """)).fetchall()
        
        potions_on_catalog = 0

    for potion in result:
        potion_amount = potion.quantity

        if potion_amount!=0 and potions_on_catalog <11:
            catalog.append({
                "sku": potion.sku,
                "name": potion.name,
                "quantity": potion.quantity,
                "price": potion.cost,
                "potion_type": [potion.red_ml, potion.green_ml, potion.blue_ml, potion.dark_ml],
            })
            potions_on_catalog+=1

    # Sort catalog by quantity in descending order and slice the top 6 potions
    catalog = sorted(catalog, key=lambda x: x['quantity'], reverse=True)[:6]

    #what exactly is in catalog
    for available in catalog:
            print(f"available potions: {available}")
    
    #else return empty
    return catalog
