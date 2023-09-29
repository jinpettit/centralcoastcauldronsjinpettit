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
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions, gold, num_red_ml FROM global_inventory WHERE id=1"))
        data = result.fetchone()

        curr_red_potions = data[0]
        gold = data[1]
        num_red_ml = data[2]

        gold += 400

        if curr_red_potions < 10:
            for barrel in barrels_delivered:
                print(barrel)
                if barrel.sku == "SMALL_RED_BARREL":
                    if (gold >= barrel.price):
                        gold -= barrel.price
                        num_red_ml += barrel.ml_per_barrel
                    else:
                        return "NOT ENOUGH GOLD"

        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = :new_gold, num_red_ml = :new_num_red_ml WHERE id=1"), {"new_gold": gold, "new_num_red_ml": num_red_ml})

    print(barrels_delivered)

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions, gold FROM global_inventory WHERE id=1"))
        data = result.fetchone()

        curr_red_potions = data[0]
        gold = data[1]

        if curr_red_potions < 10:
            for barrel in wholesale_catalog:
                if barrel.sku == "SMALL_RED_BARREL":
                    if (gold >= barrel.price):
                        return [
                            {
                                "sku": "SMALL_RED_BARREL",
                                "quantity": barrel.quantity,
                            }
                        ]

    print(wholesale_catalog)

