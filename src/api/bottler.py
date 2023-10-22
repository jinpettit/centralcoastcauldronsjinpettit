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
    green_ml_used = 0
    blue_ml_used = 0

    for potion in potions_delivered:
        red_ml_used += potion.quantity * potion.potion_type[0]
        green_ml_used += potion.quantity * potion.potion_type[1]
        blue_ml_used += potion.quantity * potion.potion_type[2]

    with db.engine.begin() as connection:   

        for potion in potions_delivered:
            result = connection.execute(sqlalchemy.text("SELECT id FROM potion_table WHERE red = :red and green = :green and blue = :blue and dark = :dark"),
                                            {"red": potion.potion_type[0], "green": potion.potion_type[1], "blue": potion.potion_type[2], "dark": potion.potion_type[3]})
            
            data = result.fetchone()

            potion_id = data[0]

            connection.execute(sqlalchemy.text("INSERT INTO potion_ledger (potion_id, potion_change) VALUES (:potion_id, :potion_change)"), 
                                {"potion_id": potion_id, "potion_change": potion.quantity})
                
        connection.execute(sqlalchemy.text("INSERT INTO ml_ledger (red_change, green_change, blue_change) VALUES (:red_ml, :green_ml, :blue_ml)"), 
                                {"red_ml": -red_ml_used, "green_ml": -green_ml_used, "blue_ml": -blue_ml_used})
        
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
            while (potions_made < 5 and row.red <= num_red_ml and row.green <= num_green_ml and row.blue <= num_blue_ml):
                potions_made += 1
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
