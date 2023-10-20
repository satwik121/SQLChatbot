import sqlite3

def convert_df_to_sql(df):
    df.rename(columns={'User ID': 'user_id',
                    'Product ID': 'product_id',
                    'Product Name' : 'product_name',
                    'Brand' : 'brand',
                    'Category' : 'category',
                    'Price' : 'price',
                    'Color' : 'color',
                    'Size' : 'size'}, inplace=True)

    conn = sqlite3.connect('fashion_db.sqlite')
    c = conn.cursor()

    c.execute('CREATE TABLE IF NOT EXISTS fashion_products (user_id int, product_id int, product_name text, brand text, category text, price int, rating float, color text, size text)')
    conn.commit()

    df.to_sql('fashion_products', conn, if_exists='replace', index = False)

    c.execute('''
    SELECT product_name FROM fashion_products LIMIT 100
            ''')
    

def read_sql_query(sql, db):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    for row in rows:
        print(row)
    conn.close()