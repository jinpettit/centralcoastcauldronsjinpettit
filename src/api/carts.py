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
    
    if sort_col is search_sort_options.customer_name:
        order_by = db.carts.c.customer
    elif sort_col is search_sort_options.item_sku:
        order_by = db.potion_table.c.sku
    elif sort_col is search_sort_options.line_item_total:
        order_by = db.cart_items.c.quantity * db.potion_table.c.price
    elif sort_col is search_sort_options.timestamp:
        order_by = db.potion_ledger.c.created_at
    else:
        assert False

    if sort_order == search_sort_order.asc:
        order_by = sqlalchemy.asc(order_by)
    if sort_order == search_sort_order.desc:
        order_by = sqlalchemy.desc(order_by)

    if search_page == "":
        page_number = 0
    else:
        page_number = int(search_page)

    table = sqlalchemy.join(db.cart_items, db.carts, db.cart_items.c.cart_id == db.carts.c.id
            ).join(db.potion_table, db.cart_items.c.potion_id == db.potion_table.c.id
            ).join(db.potion_ledger, db.potion_ledger.c.cart_items_id == db.cart_items.c.id)
        

    stmt = (sqlalchemy.select(db.carts.c.customer, db.cart_items.c.id, db.cart_items.c.created_at, db.cart_items.c.quantity, db.potion_table.c.sku, db.potion_table.c.price)
        .select_from(table)
        .limit(6)
        .offset(page_number)
        .order_by(order_by)
        .distinct())

    if customer_name != "":
        stmt = stmt.where(db.carts.c.customer.ilike(f"%{customer_name}%"))
    
    if potion_sku != "":
        stmt = stmt.where(db.potion_table.c.sku.ilike(f"%{potion_sku}%"))    

    prev = ""
    next = "" 

    with db.engine.begin() as connection:
        result = connection.execute(stmt)

        rows = result.fetchall()

        if page_number >= 5:
            prev = str(page_number - 5)

        if len(rows) > 5:
            if (prev == ""):
                next = 5
            else:
                next = str(page_number + 5) 

        results = []    

        i = 0

        for i, row in enumerate(rows):
            if i >= 5:
                break
            results.append({
                "line_item_id": row.id,
                "item_sku": row.sku,
                "customer_name": row.customer,
                "line_item_total": row.price * row.quantity,
                "timestamp": row.created_at,
            })

    return {
        "previous": prev,
        "next": next,
        "results": results
    }

class NewCart(BaseModel):
    customer: str

@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT count(*) FROM carts WHERE customer = :name"), {"name": new_cart.customer}).scalar_one()

        if (result > 0):
            result = connection.execute(sqlalchemy.text("SELECT id FROM carts WHERE customer = :name"), {"name": new_cart.customer})

        else:
            result = connection.execute(sqlalchemy.text("INSERT INTO carts (customer) VALUES (:name) RETURNING id"), {"name": new_cart.customer})

        c_id = result.scalar_one()
        
    return {"cart_id": c_id}

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

        potion_id = result.scalar_one()

        result = connection.execute(sqlalchemy.text("SELECT count(*) FROM cart_items WHERE cart_id = :cart_id and potion_id = :potion_id"), 
                                    {"cart_id": cart_id, "potion_id": potion_id}).scalar_one()
        
        if (result > 0):
            print("ok")
            connection.execute(sqlalchemy.text("UPDATE cart_items SET quantity = :quantity WHERE cart_id = :cart_id and potion_id = :potion_id"), 
                            {"cart_id": cart_id, "quantity": cart_item.quantity, "potion_id": potion_id})

        else:
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
        result = connection.execute(sqlalchemy.text("SELECT cart_items.id, cart_items.cart_id, cart_items.quantity, cart_items.potion_id, potion_table.price FROM cart_items LEFT JOIN potion_table ON cart_items.potion_id = potion_table.id WHERE cart_id = :cart_id"), 
                                    {"cart_id": cart_id})
        
        for row in result:
            payment = row.price * row.quantity

            total_payment += payment
            total_potions_bought += row.quantity

            transaction_id = connection.execute(sqlalchemy.text("INSERT INTO transactions (description) VALUES (:description) RETURNING id"), 
                                        {"description": "Checked out " + str(row.quantity) + " potions with id " + str(row.potion_id)})
        
            t_id = transaction_id.scalar_one()
            
            connection.execute(sqlalchemy.text("INSERT INTO potion_ledger (potion_id, potion_change, transaction_id, cart_items_id) VALUES (:potion_id, :potion_change, :t_id, :c_id)"), 
                    {"potion_id": row.potion_id, "potion_change": -(row.quantity), "t_id": t_id, "c_id": row.id})
            
            
            transaction_id = connection.execute(sqlalchemy.text("INSERT INTO transactions (description) VALUES (:description) RETURNING id"), 
                                        {"description": "Customer paid " + str(payment)})
        
            t_id = transaction_id.scalar_one()

            connection.execute(sqlalchemy.text("INSERT INTO gold_ledger (gold_change, transaction_id) VALUES (:payment, :t_id)"), 
                                    {"payment": payment, "t_id": t_id})
        
    print("total_potions_bought " + str(total_potions_bought) + " total_gold_paid " + str(total_payment)) 
    return {"total_potions_bought": total_potions_bought, "total_gold_paid": total_payment}
