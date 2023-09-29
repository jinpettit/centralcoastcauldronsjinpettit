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
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory WHERE id=1"))
        data = result.fetchone()

        max_items = 20

        num_red_potions = min(max_items, data[0])

        for i in range (num_red_potions):
            return [
                {
                    "sku": f"RED_POTION_{i}",
                    "name": "red potion",
                    "quantity": num_red_potions,
                    "price": 50,
                    "potion_type": [100, 0, 0, 0],
                }
            ]
