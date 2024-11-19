from fastapi import APIRouter, Depends
from pydantic import BaseModel
import random
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

    gold_price = 0
    barrel_blue_ml = 0
    barrel_red_ml = 0
    barrel_green_ml =0
    barrel_dark_ml =0
        
    for barrel in barrels_delivered:
        gold_price += (barrel.price * barrel.quantity)
        if barrel.potion_type == [1,0,0,0]:
            barrel_red_ml += barrel.ml_per_barrel * barrel.quantity
        
        elif barrel.potion_type == [0,1,0,0]:  
            barrel_green_ml += barrel.ml_per_barrel * barrel.quantity
                
        elif barrel.potion_type == [0,0,1,0]:
            barrel_blue_ml += barrel.ml_per_barrel * barrel.quantity
            
        elif barrel.potion_type == [0,0,0,1]:
            barrel_dark_ml += barrel.ml_per_barrel * barrel.quantity

    print(f"Calculated ml amounts purchased - Red: {barrel_red_ml}, Green: {barrel_green_ml}, Blue: {barrel_blue_ml}, Dark: {barrel_dark_ml}")
    print(f"Total gold spent: {gold_price}")
    
    with db.engine.begin() as connection:
        

        connection.execute(sqlalchemy.text("""
            INSERT INTO barrel_ml_log (red, green, blue, dark)
            VALUES (:barrel_red_ml, :barrel_green_ml, :barrel_blue_ml, :barrel_dark_ml)
        """), {
            "barrel_red_ml": barrel_red_ml,
            "barrel_green_ml": barrel_green_ml,
            "barrel_blue_ml": barrel_blue_ml,
            "barrel_dark_ml": barrel_dark_ml
        })

        #loosing gold because you are purchasing barrels
        connection.execute(sqlalchemy.text("""
           INSERT INTO gold_tracker(gold)
            VALUES (:gold_price)
            """), {"gold_price": - gold_price })
    return "OK"

# Gets called once a day , try buying equal amounts of ml in barrels

@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    # Print and shuffle wholesale catalog
    print("Wholesale Catalog:", wholesale_catalog)
    random.shuffle(wholesale_catalog)

    with db.engine.begin() as connection:
        # Get current ml totals and gold amount
        result_barrel = connection.execute(sqlalchemy.text("""
            SELECT COALESCE(SUM(red), 0) AS red_ml,
                COALESCE(SUM(green), 0) AS green_ml,
                COALESCE(SUM(blue), 0) AS blue_ml,                                 
                COALESCE(SUM(dark), 0) AS dark_ml                                 
            FROM barrel_ml_log
                """)).fetchone()
        
        result_gold = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(gold), 0) AS total_gold FROM gold_tracker")).fetchone()
    gold_amount = result_gold.total_gold

    # Inventory types and maximum ml allowed for each type
    local_barrels = {
        'red': {'ml': result_barrel.red_ml, 'color_vector': [1, 0, 0, 0]},
        'green': {'ml': result_barrel.green_ml, 'color_vector': [0, 1, 0, 0]},
        'blue': {'ml': result_barrel.blue_ml, 'color_vector': [0, 0, 1, 0]},
        'dark': {'ml': result_barrel.dark_ml, 'color_vector': [0, 0, 0, 1]}
    }

    TARGET_ML = 5000  # Fixed target for each potion type
    barrels_to_purchase = []

    # Iterate until you either run out of gold or all potion types reach TARGET_ML
    while gold_amount > 1000:
        purchase_made = False  # Track if a purchase is made in this loop
        
        # Iterate through each potion type with its current ml
        for ml_to_buy, properties in local_barrels.items():
            if properties['ml'] >= TARGET_ML:
                continue  # Skip types already at or above the target
            
            # Find all barrels matching the potion type, sorted by price (ascending)
            matching_barrels = sorted(
                [b for b in wholesale_catalog if b.potion_type == properties['color_vector']],
                key=lambda x: x.price
            )
            
            # Attempt to purchase a suitable barrel
            for barrel in matching_barrels:
                # Check affordability and if the barrel has stock
                if barrel.price <= gold_amount and barrel.quantity > 0 and "mini" not in barrel.sku.lower():
                    barrels_needed = (TARGET_ML - properties['ml']) // barrel.ml_per_barrel
                    barrels_to_buy = min(barrels_needed, barrel.quantity)  # Max barrels to buy
                    
                    if barrels_to_buy > 0:
                        # Add barrels to purchase list
                        barrels_to_purchase.append({
                            "sku": barrel.sku,
                            "quantity": barrels_to_buy
                        })
                        
                        # Update resources
                        gold_amount -= barrel.price * barrels_to_buy
                        properties['ml'] += barrel.ml_per_barrel * barrels_to_buy
                        barrel.quantity -= barrels_to_buy
                        purchase_made = True  # A purchase was made
                        
                        # Log the purchase
                        print(f"Purchased {barrels_to_buy} barrel(s) of {barrel.sku} for {ml_to_buy}.")
                        print(f"Remaining gold: {gold_amount}")
                        print(f"New ml for {ml_to_buy}: {properties['ml']}")
                        
                        break  # Move to the next potion type after a purchase
        
        if not purchase_made:
            print("No more barrels can be purchased within the constraints.")
            break  # Exit loop if no purchases can be made

    # Output all purchases
    print("Barrels purchased:")
    for purchase in barrels_to_purchase:
        print(f"SKU: {purchase['sku']}, Quantity: {purchase['quantity']}")

    return barrels_to_purchase


    # return barrels_to_purchase
