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

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """
    print(barrels_delivered)
    
    red_ml = 0
    blue_ml = 0
    green_ml = 0
    dark_ml = 0
    gold_spent = 0
    
    for barrel in barrels_delivered:
        gold_spent += barrel.price * barrel.quantity
        if barrel.potion_type == [1, 0, 0, 0]:
            red_ml += barrel.ml_per_barrel * barrel.quantity
        elif barrel.potion_type == [0, 1, 0, 0]:
            green_ml += barrel.ml_per_barrel * barrel.quantity
        elif barrel.potion_type == [0, 0, 1, 0]:
            blue_ml += barrel.ml_per_barrel * barrel.quantity
        elif barrel.potion_type == [0, 0, 0, 1]:
            dark_ml += barrel.ml_per_barrel * barrel.quantity

    with db.engine.begin() as connection:

        transaction_id = connection.execute(sqlalchemy.text("INSERT INTO transactions (description) VALUES (:description) RETURNING id"), 
                                            {"description": "RED_ML delivered " + str(red_ml) + ", GREEN_ML delivered " + str(green_ml) + ", BLUE_ML delivered " + str(blue_ml) + ", BLUE_ML delivered " + str(dark_ml)})
        
        t_id = transaction_id.scalar_one()

        connection.execute(sqlalchemy.text("INSERT INTO ml_ledger (red_change, green_change, blue_change, dark_change, transaction_id) VALUES (:red_ml, :green_ml, :blue_ml, :dark_ml, :t_id)"), 
                                   {"red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "dark_ml": dark_ml, "t_id": t_id})
        
        transaction_id = connection.execute(sqlalchemy.text("INSERT INTO transactions (description) VALUES (:description) RETURNING id"), 
                                            {"description": "Barrels purchase " + str(gold_spent) + " GOLD"})
        
        t_id = transaction_id.scalar_one()

        connection.execute(sqlalchemy.text("INSERT INTO gold_ledger (gold_change, transaction_id) VALUES (:gold_spent, :t_id)"), 
                                   {"gold_spent": -gold_spent, "t_id": t_id})

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(gold_change), 0) FROM gold_ledger"))
        data = result.fetchone()

        gold = data[0]

        barrel_list = []

        for barrel in wholesale_catalog:
            if gold >= barrel.price:
                    gold -= barrel.price
                    barrel_list.append({
                            "sku": barrel.sku,
                            "quantity": 1,
                        })
        
        print(barrel_list)
        return barrel_list



