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

class NewCart(BaseModel):
    customer: str

@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("INSERT INTO carts (customer) VALUES (:name) RETURNING id"), {"name": new_cart.customer})

        data = result.fetchone()
        
    return {"cart_id": data[0]}

@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """


class CartItem(BaseModel):
    quantity: int

@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT id FROM potion_table WHERE sku = :item_sku"), 
                                    {"item_sku": item_sku})

        data = result.fetchone()

        potion_id = data[0]
        
        connection.execute(sqlalchemy.text("INSERT INTO cart_items (cart_id, quantity, potion_id) VALUES (:cart_id, :quantity, :potion_id)"), 
                                    {"cart_id": cart_id, "quantity": cart_item.quantity, "potion_id": potion_id})
        
    print(potion_id)
    return "OK"

class CartCheckout(BaseModel):
    payment: str


@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    total_payment = 0
    total_potions_bought = 0
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT cart_items.cart_id, cart_items.quantity, cart_items.potion_id, potion_table.price FROM cart_items LEFT JOIN potion_table ON cart_items.potion_id = potion_table.id WHERE cart_id = :cart_id"), 
                                    {"cart_id": cart_id})
        
        for row in result:
            payment = row.price * row.quantity

            total_payment += payment
            total_potions_bought += row.quantity

            connection.execute(sqlalchemy.text("INSERT INTO potion_ledger (potion_id, potion_change) VALUES (:potion_id, potion_change)"), 
                                    {"potion_id": -row.potion_id, "potion_change": row.quantity})

            connection.execute(sqlalchemy.text("INSERT INTO gold_ledger (gold_change) VALUES (:payment)"), 
                                    {"payment": payment})
        
            connection.execute(sqlalchemy.text("DELETE FROM cart_items WHERE cart_id = :cart_id"), 
                                                {"cart_id": cart_id})
            
            connection.execute(sqlalchemy.text("DELETE FROM carts WHERE id = :id"), 
                                                {"id": cart_id})
        
    print("total_potions_bought " + str(total_potions_bought) + " total_gold_paid " + str(payment)) 
    return {"total_potions_bought": total_potions_bought, "total_gold_paid": payment}
