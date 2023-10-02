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

class Item:
    def __init__(self, item_sku, quantity):
        self.item_sku = item_sku
        self.quantity = quantity

class NewCart(BaseModel):
    customer: str

@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    global curr_cart_id
    curr_cart_id += 1
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
    total_carts.update({cart_id : Item(item_sku, cart_item.quantity)})
    return "OK"

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    item_sku = total_carts[cart_id].item_sku
    item_quantity = total_carts[cart_id].quantity

    print(item_sku)
    print(item_quantity)

    if item_sku == "RED_POTION":
        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("SELECT num_red_potions, gold FROM global_inventory WHERE id=1"))
            data = result.fetchone()

            num_red_potions = data[0] - item_quantity

            print(num_red_potions)

            if (num_red_potions < 0):
                del total_carts[cart_id]
                return "NOT ENOUGH RED POTIONS IN INVENTORY"
            
            payment = (item_quantity * 50)
            
            gold = data[1] + payment

            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = :num_red_potions, gold = :gold WHERE id=1"), 
                            {"num_red_potions": num_red_potions,"gold": gold})

    del total_carts[cart_id]

    return {"total_potions_bought": item_quantity, "total_gold_paid": payment}
