from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(potion_change), 0) FROM potion_ledger"))
        total_potions = result.scalar_one()

        result = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(red_change + green_change + blue_change + dark_change), 0) FROM ml_ledger"))
        total_ml = result.scalar_one()

        result = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(gold_change), 0) FROM gold_ledger"))
        total_gold = result.scalar_one()

    return {"num_of_potions": total_potions, 
            "ml_in_barrels": total_ml,
            "gold": total_gold}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
