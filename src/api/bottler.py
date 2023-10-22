from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_potions(potions_delivered: list[PotionInventory]):
    """ """

    with db.engine.begin() as connection:   
        result = connection.execute(sqlalchemy.text("SELECT * FROM potion_table"))

        for row in result:
            for potion in potions_delivered:
                if (potion.potion_type == [row.red, row.green, row.blue, row.dark]):
                    red_ml_used = row.red * potion.quantity
                    green_ml_used = row.green * potion.quantity
                    blue_ml_used = row.blue * potion.quantity

                    connection.execute(sqlalchemy.text("UPDATE potion_table SET quantity = quantity + :potion_quantity WHERE sku = :sku"), {"potion_quantity": potion.quantity, "sku": row.sku})

                    connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml - :new_num_red_ml, num_green_ml = num_green_ml - :new_num_green_ml, num_blue_ml = num_blue_ml - :new_num_blue_ml, total_potions = total_potions + :potions_quantity WHERE id=1"), 
                                {"new_num_red_ml": red_ml_used,
                                "new_num_green_ml": green_ml_used, 
                                "new_num_blue_ml": blue_ml_used,
                                "potions_quantity": potion.quantity})
    return "OK" 

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(red_change),0) AS red_ml, COALESCE(SUM(green_change),0) AS green_ml, COALESCE(SUM(blue_change),0) AS blue_ml, COALESCE(SUM(dark_change),0) AS dark_ml FROM ml_ledger"))
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory WHERE id=1"))
        
        data = result.fetchone()

        num_red_ml = data.num_red_ml
        num_green_ml = data.num_green_ml
        num_blue_ml = data.num_blue_ml

        potions = connection.execute(sqlalchemy.text("SELECT * FROM potion_table"))

        potion_list = []

        for row in potions:
            potions_made = 0
            while (potions_made < 5 and row.red <= num_red_ml and row.green <= num_green_ml and row.red <= num_blue_ml):
                num_red_ml -= row.red
                num_green_ml -= row.green
                num_blue_ml -= row.blue

            if (potions_made > 0):
                potion_list.append({
                        "potion_type": [row.red, row.green, row.blue, row.dark],
                        "quantity": potions_made,
                    })

        print(potion_list)
        return potion_list
