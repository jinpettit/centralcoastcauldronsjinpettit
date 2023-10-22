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
        result = connection.execute(sqlalchemy.text("SELECT * FROM potion_table"))

        catalog_list = []
        for row in result:
            sum_potions = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(potion_change), 0) FROM potion_ledger WHERE potion_id = :potion:id"), {"potion_id": row.id}) 

            potions = sum_potions.scalar_one()

            if potions > 0:
                catalog_list.append({
                    "sku": row.sku,
                    "name": row.name,
                    "quantity": potions,
                    "price": row.price,
                    "potion_type": [row.red, row.green, row.blue, row.dark],
                })
        print(catalog_list)
        return catalog_list
            
