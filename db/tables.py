import mariadb

tables = {
    "stocks": """
        CREATE TABLE stocks (
            id INT NOT NULL AUTO_INCREMENT,
            stock_name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id)
        )
    """,
    "prices": """
        CREATE TABLE prices (
            stock_id INT NOT NULL,
            valid_after TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            price DECIMAL(65,2) NOT NULL,
            FOREIGN KEY (stock_id) REFERENCES stocks(id),
            PRIMARY KEY (stock_id, valid_after)
        )
    """,
    "transactions": """
        CREATE TABLE transactions (
            id INT NOT NULL AUTO_INCREMENT,
            stock_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            purchase_amount INT NOT NULL,
            total_purchase_price DECIMAL(65,2),
            FOREIGN KEY (stock_id) REFERENCES stocks(id),
            PRIMARY KEY (id)
        )
    """,
}


def _drop_tables(db, fail_on_missing=True):
    cursor = db.cursor()
    drop_stmt = """DROP TABLE {};"""
    check_stmt = """
        SELECT COUNT(*)
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ?
    """
    num_tables = 0
    try:
        for table in reversed(tables):
            if not fail_on_missing:
                cursor.execute(check_stmt, (table,))
                if cursor.fetchone()[0] == 0:
                    continue
            cursor.execute(drop_stmt.format(table))
            num_tables += 1
    except mariadb.Error as e:
        cursor.close()
        raise Exception("Error dropping tables.\n"
                        f"SQL: {cursor.statment}\n"
                        f"Error: {e}") from e
    cursor.close()
    return num_tables


def _create_tables(db):
    cursor = db.cursor()
    num_tables = 0
    try:
        for table, sql in tables.items():
            cursor.execute(sql)
            num_tables += 1
    except mariadb.Error as e:
        cursor.close()
        raise Exception(f"Error creating table '{table}'.\nSQL: {sql}\n"
                        f"Error: {e}") from e
    cursor.close()
    return num_tables
