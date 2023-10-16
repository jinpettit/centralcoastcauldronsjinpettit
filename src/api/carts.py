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
        result = connection.execute(sqlalchemy.text("SELECT * FROM cart_items LEFT JOIN potion_table ON cart_items.potion_id = potion_table.id WHERE cart_id = :cart_id"), 
                                    {"cart_id": cart_id})
        
        for row in result:
            payment = row.price * row.quantity

            total_payment += payment
            total_potions_bought += row.quantity

            connection.execute(sqlalchemy.text("UPDATE potion_table SET quantity = quantity - :potions WHERE id = :potion_id"), 
                                                {"potions": row.quantity, "potion_id": row.potion_id})

            connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold + :payment, total_potions = total_potions - :potions"), 
                                                {"payment": payment, "potions": row.quantity})
            
            connection.execute(sqlalchemy.text("DELETE FROM cart_items WHERE cart_id = :cart_id"), 
                                                {"cart_id": cart_id})
            
            connection.execute(sqlalchemy.text("DELETE FROM carts WHERE id = :id"), 
                                                {"id": cart_id})
        
    print("total_potions_bought " + str(total_potions_bought) + " total_gold_paid " + str(payment)) 
    return {"total_potions_bought": total_potions_bought, "total_gold_paid": payment}

    '''
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

    print("RED BOUGHT " + str(red_potions_purchase) + " GREEN BOUGHT " + str(green_potions_purchase) + " BLUE BOUGHT" + str(blue_potions_purchase))
    print("total_potions_bought " + str(total_potions_bought) + " total_gold_paid " + str(payment)) 

    return {"total_potions_bought": total_potions_bought, "total_gold_paid": payment}
    '''
