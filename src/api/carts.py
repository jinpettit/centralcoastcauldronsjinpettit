from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from enum import Enum

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }

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

            transaction_id = connection.execute(sqlalchemy.text("INSERT INTO transactions (description) VALUES (:description) RETURNING id"), 
                                        {"description": "Checked out " + str(row.quantity) + " potions with id " + str(row.potion_id)})
        
            t_id = transaction_id.scalar_one()
            
            connection.execute(sqlalchemy.text("INSERT INTO potion_ledger (potion_id, potion_change, transaction_id) VALUES (:potion_id, :potion_change, :t_id)"), 
                    {"potion_id": row.potion_id, "potion_change": -(row.quantity), "t_id": t_id})
            
            
            transaction_id = connection.execute(sqlalchemy.text("INSERT INTO transactions (description) VALUES (:description) RETURNING id"), 
                                        {"description": "Customer paid " + str(payment)})
        
            t_id = transaction_id.scalar_one()

            connection.execute(sqlalchemy.text("INSERT INTO gold_ledger (gold_change, transaction_id) VALUES (:payment, :t_id)"), 
                                    {"payment": payment, "t_id": t_id})
        
            connection.execute(sqlalchemy.text("DELETE FROM cart_items WHERE cart_id = :cart_id"), 
                                                {"cart_id": cart_id})
            
            connection.execute(sqlalchemy.text("DELETE FROM carts WHERE id = :id"), 
                                                {"id": cart_id})
        
    print("total_potions_bought " + str(total_potions_bought) + " total_gold_paid " + str(payment)) 
    return {"total_potions_bought": total_potions_bought, "total_gold_paid": payment}
