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


def get_product_categories(connection):
    cursor = connection.execute(
        """
        SELECT
            category_id,
            category_description
        FROM categories
        ORDER BY category_description
        """
    )

    return cursor.fetchall()

def display_options(all_options, title, option_type):
    option_ids = []

    print(f"\n{title}")

    for option_number, option in enumerate(all_options, start=1):
        option_id = option[0]
        option_description = option[1]

        print(f"{option_number}. {option_description}")
        option_ids.append(option_id)

    while True:
        selected_option = get_valid_integer(
            f"Enter the number against the {option_type} you want to choose: "
        )

        if 1 <= selected_option <= len(option_ids):
            return option_ids[selected_option - 1]

        print("Please enter a valid option number.")

def select_product_category(connection):
    categories = get_product_categories(connection)

    return display_options(
        categories,
        "Product Categories",
        "product category"
    )

def get_available_products(connection, category_id):
    cursor = connection.execute(
        """
        SELECT
            product_id,
            product_description
        FROM products
        WHERE category_id = ?
        AND product_status = 'Available'
        ORDER BY product_description
        """,
        (category_id,)
    )

    return cursor.fetchall()

def select_product(connection, category_id):
    products = get_available_products(
        connection,
        category_id
    )

    return display_options(
        products,
        "Available Products",
        "product"
    )

def get_product_sellers(connection, product_id):
    cursor = connection.execute(
        """
        SELECT
            s.seller_id,
            s.seller_name || ' - £' || printf('%.2f', ps.price)
        FROM product_sellers AS ps
        JOIN sellers AS s
            ON ps.seller_id = s.seller_id
        WHERE ps.product_id = ?
        ORDER BY s.seller_name
        """,
        (product_id,)
    )

    return cursor.fetchall()

def select_seller(connection, product_id):
    sellers = get_product_sellers(
        connection,
        product_id
    )

    return display_options(
        sellers,
        "Available Sellers",
        "seller"
    )

def get_valid_quantity():
    while True:
        quantity = get_valid_integer(
            "Enter the quantity you want to order: "
        )

        if quantity > 0:
            return quantity

        print("The quantity must be greater than 0")


def get_selected_product_price(connection, product_id, seller_id):
    cursor = connection.execute(
        """
        SELECT price
        FROM product_sellers
        WHERE product_id = ?
        AND seller_id = ?
        """,
        (product_id, seller_id)
    )

    result = cursor.fetchone()

    return result[0]

def add_item_to_basket(
    connection,
    basket_id,
    product_id,
    seller_id,
    quantity,
    price
):
    try:
        connection.execute(
            """
            INSERT INTO basket_contents
            (
                basket_id,
                product_id,
                seller_id,
                quantity,
                price
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                basket_id,
                product_id,
                seller_id,
                quantity,
                price
            )
        )

        connection.commit()

    except sqlite3.IntegrityError:
        connection.rollback()
        print("This product is already in your basket.")
        return False

    return True


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



            elif menu_choice == 2:

                selected_category_id = select_product_category(connection)

                selected_product_id = select_product(

                    connection,

                    selected_category_id

                )

                selected_seller_id = select_seller(

                    connection,

                    selected_product_id

                )

                quantity = get_valid_quantity()

                selected_price = get_selected_product_price(
                    connection,
                    selected_product_id,
                    selected_seller_id
                )

                print(f"Selected price: £{selected_price:.2f}")

                item_added = add_item_to_basket(
                    connection,
                    current_basket_id,
                    selected_product_id,
                    selected_seller_id,
                    quantity,
                    selected_price
                )

                if item_added:
                    print("Item added to your basket")


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


