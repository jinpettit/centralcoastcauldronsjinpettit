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
    print(potions_delivered)

    for potion in potions_delivered:
        if (potion.potion_type[0] == 100):
            with db.engine.begin() as connection:   
                result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_red_potions FROM global_inventory WHERE id=1"))

                data = result.fetchone()

                num_red_ml = data[0]
                num_red_potions = data[1]

                curr_red_potions = potion.quantity + num_red_potions

                new_num_red_ml = num_red_ml - (potion.quantity * 100)
    
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = :new_num_red_ml, num_red_potions = :curr_red_potions WHERE id=1"), 
                            {"new_num_red_ml": new_num_red_ml,"curr_red_potions": curr_red_potions})


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
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory WHERE id=1"))

        data = result.fetchone()

        num_red_ml = data[0]

        new_num_red_potions = (num_red_ml / 100)

        return [
                {
                    "potion_type": [100, 0, 0, 0],
                    "quantity": new_num_red_potions,
                }
            ]
