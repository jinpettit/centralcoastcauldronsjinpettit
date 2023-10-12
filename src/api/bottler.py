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
    red_ml_used = 0
    curr_red_potions = 0
    green_ml_used = 0
    curr_green_potions = 0
    blue_ml_used = 0
    curr_blue_potions = 0

    for potion in potions_delivered:
        if potion.potion_type[0] == 100:
            red_ml_used = (potion.quantity * 100)
            curr_red_potions = potion.quantity
        elif potion.potion_type[1] == 100:
            green_ml_used = (potion.quantity * 100)
            curr_green_potions = potion.quantity
        elif potion.potion_type[2] == 100:
            blue_ml_used = (potion.quantity * 100)
            curr_blue_potions = potion.quantity

    with db.engine.begin() as connection:   

        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory WHERE id=1"))

        data = result.fetchone()

        new_num_red_ml = data.num_red_ml - red_ml_used
        total_red_potions = data.num_red_potions + curr_red_potions

        new_num_green_ml = data.num_green_ml - green_ml_used
        total_green_potions = data.num_green_potions + curr_green_potions

        new_num_blue_ml = data.num_blue_ml - blue_ml_used
        total_blue_potions = data.num_blue_potions + curr_blue_potions

        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = :new_num_red_ml, num_red_potions = :curr_red_potions, num_green_ml = :new_num_green_ml, num_green_potions = :curr_green_potions, num_blue_ml = :new_num_blue_ml, num_blue_potions = :curr_blue_potions WHERE id=1"), 
                    {"new_num_red_ml": new_num_red_ml,"curr_red_potions": total_red_potions, 
                     "new_num_green_ml": new_num_green_ml,"curr_green_potions": total_green_potions, 
                     "new_num_blue_ml": new_num_blue_ml,"curr_blue_potions": total_blue_potions})

    print("RED_ML: " + str(new_num_green_ml) + " RED_POTION: " + str(total_red_potions) + " GREEN_ML: " + str(new_num_green_ml) + " GREEN_POTION: " + str(total_green_potions) + " BLUE_ML: " + str(new_num_green_ml) + " BLUE_POTION: " + str(total_blue_potions))
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
        new_num_purple_potions = min((num_red_ml // 50), (num_blue_ml // 50))

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
