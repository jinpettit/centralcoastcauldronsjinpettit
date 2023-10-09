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
    gold_spent = 0
    
    for barrel in barrels_delivered:
        gold_spent += barrel.price * barrel.quantity
        if barrel.sku == "SMALL_RED_BARREL":
            red_ml = barrel.ml_per_barrel * barrel.quantity
        elif barrel.sku == "SMALL_BLUE_BARREL":
            blue_ml = barrel.ml_per_barrel * barrel.quantity
        elif barrel.sku == "SMALL_GREEN_BARREL":
            green_ml = barrel.ml_per_barrel * barrel.quantity

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory WHERE id=1"))
        data = result.fetchone()

        gold = data.gold - gold_spent
        num_red_ml = data.num_red_ml + red_ml
        num_blue_ml = data.num_blue_ml + blue_ml
        num_green_ml = data.num_green_ml + green_ml

        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = :new_gold, num_red_ml = :new_num_red_ml, num_blue_ml = :new_num_blue_ml, num_green_ml = :new_num_green_ml WHERE id=1"), 
                           {"new_gold": gold, "new_num_red_ml": num_red_ml, "new_num_blue_ml": num_blue_ml, "new_num_green_ml": num_green_ml})

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory WHERE id=1"))
        data = result.fetchone()

        gold = data.gold

        barrel_list = []

        for barrel in wholesale_catalog:
            if barrel.sku == "SMALL_RED_BARREL" and gold >= barrel.price:
                    gold -= barrel.price
                    barrel_list.append({
                            "sku": "SMALL_RED_BARREL",
                            "quantity": 1,
                        })
            if barrel.sku == "SMALL_BLUE_BARREL" and gold >= barrel.price:
                    gold -= barrel.price
                    barrel_list.append({
                            "sku": "SMALL_BLUE_BARREL",
                            "quantity": 1,
                        })
            if barrel.sku == "SMALL_GREEN_BARREL" and gold >= barrel.price:
                    gold -= barrel.price
                    barrel_list.append({
                            "sku": "SMALL_GREEN_BARREL",
                            "quantity": 1,
                        })

        return barrel_list



