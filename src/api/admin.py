from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    with db.engine.begin() as connection:

        # Delete all previous records in the tables
        connection.execute(sqlalchemy.text("DELETE FROM gold_tracker"))
        connection.execute(sqlalchemy.text("DELETE FROM potion_log"))
        connection.execute(sqlalchemy.text("DELETE FROM barrel_ml_log"))

         # Insert the new records with the updated values
        connection.execute(sqlalchemy.text("INSERT INTO gold_tracker (gold) VALUES (100)"))
    
        
        
        # Reset the barrel inventory
        connection.execute(sqlalchemy.text("""
            INSERT INTO barrel_ml_log (red, green, blue, dark)
            VALUES (0, 0, 0, 0)"""))
