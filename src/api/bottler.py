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
                    red_ml_used = row.red * row.quantity
                    green_ml_used = row.green * row.quantity
                    blue_ml_used = row.blue * row.quantity

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
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory WHERE id=1"))
        
        data = result.fetchone()

        potions_dic = {}

        num_red_ml = data.num_red_ml
        num_green_ml = data.num_green_ml
        num_blue_ml = data.num_blue_ml

        new_num_red_potions = (num_red_ml // 100) // 2
        new_num_green_potions = (num_green_ml // 100) 
        new_num_blue_potions = (num_blue_ml // 100) // 2
        new_num_purple_potions = min((num_red_ml // 100), (num_blue_ml // 100))

        potions_dic["RED_POTION"] = new_num_red_potions
        potions_dic["GREEN_POTION"] = new_num_green_potions
        potions_dic["BLUE_POTION"] = new_num_blue_potions
        potions_dic["PURPLE_POTION"] = new_num_purple_potions

        total_potions = new_num_red_potions + new_num_blue_potions + new_num_green_potions + new_num_purple_potions
        potion_list = []
        if total_potions > 0:
            potions = connection.execute(sqlalchemy.text("SELECT * FROM potion_table"))
            for row in potions:
                if potions_dic[row.sku] > 0:
                    potion_list.append({
                        "potion_type": [row.red, row.green, row.blue, row.dark],
                        "quantity": potions_dic[row.sku],
                    })
        print(potion_list)
        return potion_list
