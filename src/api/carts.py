from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

total_carts = {}
curr_cart_id = 0


class NewCart(BaseModel):
    customer: str

@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    global curr_cart_id
    curr_cart_id += 1
    total_carts[curr_cart_id] = {}
    return {"cart_id": curr_cart_id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    return {total_carts[cart_id]}


class CartItem(BaseModel):
    quantity: int

@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    total_carts[cart_id].update({item_sku : cart_item.quantity})
    return "OK"

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    payment = 0
    red_potions_purchase = 0
    green_potions_purchase = 0
    blue_potions_purchase = 0

    for potion in total_carts[cart_id].keys():
        if potion == "RED_POTION":
            red_potions_purchase = total_carts[cart_id][potion]
        if potion == "GREEN_POTION":
            green_potions_purchase = total_carts[cart_id][potion]
        if potion == "BLUE_POTION":
            blue_potions_purchase = total_carts[cart_id][potion]

    payment = (red_potions_purchase * 50) + (green_potions_purchase * 50) + (blue_potions_purchase * 60)
    total_potions_bought = red_potions_purchase + green_potions_purchase + blue_potions_purchase

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory WHERE id=1"))
        data = result.fetchone()

        num_red_potions = data.num_red_potions - red_potions_purchase
        num_green_potions = data.num_green_potions - green_potions_purchase
        num_blue_potions = data.num_blue_potions - blue_potions_purchase

        if num_red_potions < 0 or num_blue_potions < 0 or num_green_potions < 0:
            total_carts.pop(cart_id)
            return "NOT ENOUGH POTIONS IN INVENTORY"
        
        gold = data.gold + payment

        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = :num_red_potions, num_green_potions = :num_green_potions, num_blue_potions = :num_blue_potions,gold = :gold WHERE id=1"), 
                        {"num_red_potions": num_red_potions, "num_green_potions": num_green_potions, "num_blue_potions": num_blue_potions, "gold": gold})
            

    total_carts.pop(cart_id)

    print("RED BOUGHT " + num_red_potions + " GREEN BOUGHT " + num_green_potions + " BLUE BOUGHT" + num_green_potions)
    print("total_potions_bought " + total_potions_bought + " total_gold_paid " + payment) 

    return {"total_potions_bought": total_potions_bought, "total_gold_paid": payment}
