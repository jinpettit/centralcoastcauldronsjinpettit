from fastapi import APIRouter
import sqlalchemy
from src import database as db
router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    # Can return a max of 20 items.

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory WHERE id=1"))
        potion = connection.execute(sqlalchemy.text("SELECT * FROM potion_table"))
        data = result.fetchone()

        for row in potion:
            print(row)
            
        num_red_potions = data.num_red_potions
        num_green_potions = data.num_green_potions
        num_blue_potions = data.num_blue_potions



        catalog_list = []

        if num_red_potions > 0:
            catalog_list.append({
                "sku": "RED_POTION",
                "name": "red potion",
                "quantity": num_red_potions,
                "price": 50,
                "potion_type": [100, 0, 0, 0],
            })
        if num_green_potions > 0:
            catalog_list.append({
                "sku": "GREEN_POTION",
                "name": "green potion",
                "quantity": num_green_potions,
                "price": 50,
                "potion_type": [0, 100, 0, 0],
            })
        if num_blue_potions > 0:
            catalog_list.append({
                "sku": "BLUE_POTION",
                "name": "blue potion",
                "quantity": num_blue_potions,
                "price": 60,
                "potion_type": [0, 0, 100, 0],
            })
        print(catalog_list)
        return catalog_list
            
