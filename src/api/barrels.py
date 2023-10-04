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
    
    for barrel in barrels_delivered:
        if barrel.sku == "SMALL_RED_BARREL":
            red_ml = barrel.ml_per_barrel
            gold_spent = barrel.price
            with db.engine.begin() as connection:
                result = connection.execute(sqlalchemy.text("SELECT gold, num_red_ml FROM global_inventory WHERE id=1"))
                data = result.fetchone()

                gold = data[0] - gold_spent
                num_red_ml = data[1] + red_ml

                connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = :new_gold, num_red_ml = :new_num_red_ml WHERE id=1"), {"new_gold": gold, "new_num_red_ml": num_red_ml})

            break

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory WHERE id=1"))
        data = result.fetchone()

        curr_red_potions = data.num_red_potions
        gold = data.gold

        lst = []
        for barrel in wholesale_catalog:
            if barrel.sku == "SMALL_RED_BARREL":
                if gold >= barrel.price:
                    gold -= barrel.price
                    lst.append({
                            "sku": "SMALL_RED_BARREL",
                            "quantity": 1,
                        })
            '''
            if barrel.sku == "SMALL_BLUE_BARREL":
                if gold >= barrel.price:
                    gold -= barrel.price
                    lst.append({
                            "sku": "SMALL_BLUE_BARREL",
                            "quantity": 1,
                        })
            if barrel.sku == "SMALL_GREEN_BARREL":
                if gold >= barrel.price:
                    gold -= barrel.price
                    lst.append({
                            "sku": "SMALL_GREEN_BARREL",
                            "quantity": 1,
                        })
            '''
        return lst



