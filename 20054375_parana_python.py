import sqlite3


DATABASE_NAME = "20054375_parana_python_working.db"

def connect_database():
    connection = sqlite3.connect(DATABASE_NAME)
    return connection

def enable_foreign_keys(connection):
    connection.execute("PRAGMA foreign_keys = ON")
    foreign_keys_status = connection.execute(
        "PRAGMA foreign_keys"
    ).fetchone()[0]
    return foreign_keys_status

def get_valid_integer(prompt):
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Please enter a whole number.")

def get_shopper(connection, shopper_id):
    cursor = connection.execute(
        """
        SELECT shopper_first_name
        FROM shoppers
        WHERE shopper_id = ?
        """,
        (shopper_id,)
    )
    return cursor.fetchone()

def get_or_create_current_basket(connection, shopper_id):
    cursor = connection.execute(
        """
        SELECT basket_id
        FROM shopper_baskets
        WHERE shopper_id = ?
          AND DATE(basket_created_date_time) = DATE('now')
        ORDER BY basket_created_date_time DESC
        LIMIT 1
        """,
        (shopper_id,)
    )

    basket = cursor.fetchone()

    if basket is not None:
        return basket[0]

    sequence_row = connection.execute(
        """
        SELECT seq
        FROM sqlite_sequence
        WHERE name = ?
        """,
        ("shopper_baskets",)
    ).fetchone()

    if sequence_row is None:
        new_basket_id = 1
    else:
        new_basket_id = sequence_row[0] + 1

    try:
        connection.execute(
            """
            INSERT INTO shopper_baskets
            (
                basket_id,
                shopper_id,
                basket_created_date_time
            )
            VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
            (new_basket_id, shopper_id)
        )
        connection.commit()

    except sqlite3.Error:
        connection.rollback()
        raise

    return new_basket_id

def display_main_menu():
    print("\nPARANA - SHOPPER MAIN MENU")
    print("-" * 30)
    print("[1] Display your order history")
    print("[2] Add an item to your basket")
    print("[3] View your basket")
    print("[4] Change the quantity of an item in your basket")
    print("[5] Remove an item from your basket")
    print("[6] Checkout")
    print("[7] Exit")

def get_menu_choice():
    while True:
        choice = get_valid_integer(
            "Enter the number against the menu option you want to choose: "
        )

        if 1 <= choice <= 7:
            return choice

        print("Please enter a number between 1 and 7.")

def get_order_history(connection, shopper_id):
    cursor = connection.execute(
        """
        SELECT
            so.order_id,
            so.order_date,
            p.product_description,
            s.seller_name,
            op.price,
            op.quantity,
            op.ordered_product_status
        FROM shopper_orders AS so
        JOIN ordered_products AS op
            ON so.order_id = op.order_id
        JOIN products AS p
            ON op.product_id = p.product_id
        JOIN sellers AS s
            ON op.seller_id = s.seller_id
        WHERE so.shopper_id = ?
        ORDER BY so.order_date DESC, so.order_id DESC
        """,
        (shopper_id,)
    )

    return cursor.fetchall()

def display_order_history(connection, shopper_id):
    orders = get_order_history(connection, shopper_id)

    if not orders:
        print("\nNo orders placed by this customer")
        return

    print("\nORDER HISTORY")
    print("-" * 60)

    current_order_id = None

    for order in orders:
        (
            order_id,
            order_date,
            product_description,
            seller_name,
            price,
            quantity,
            ordered_product_status
        ) = order

        if order_id != current_order_id:
            if current_order_id is not None:
                print()

            print(f"Order ID: {order_id}")
            print(f"Order date: {order_date}")
            current_order_id = order_id

        print(f"Product: {product_description}")
        print(f"Seller: {seller_name}")
        print(f"Price: £{price:.2f}")
        print(f"Quantity: {quantity}")
        print(f"Status: {ordered_product_status}")
        print("-" * 60)

def main():
    connection = None

    try:
        connection = connect_database()
        foreign_keys_status = enable_foreign_keys(connection)
        print(f"Foreign keys enabled: {foreign_keys_status}")

        shopper_id = get_valid_integer("Enter shopper ID: ")
        shopper = get_shopper(connection, shopper_id)

        if shopper is None:
            print("Shopper not found.")
            return

        print(f"Welcome {shopper[0]}")
        current_basket_id = get_or_create_current_basket(
            connection,
            shopper_id
        )
        print(f"Current basket ID: {current_basket_id}")
        while True:
            display_main_menu()
            menu_choice = get_menu_choice()

            if menu_choice == 1:
                display_order_history(connection, shopper_id)

            elif menu_choice == 7:
                print("Goodbye.")
                break

    except sqlite3.Error as error:
        print(f"Database error: {error}")

    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()


