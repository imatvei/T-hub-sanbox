import requests as req
import pandas as pd
from pandas.api.types import infer_dtype
import psycopg2 as ps
from psycopg2 import sql
import traceback

URL_API = 'https://raw.githubusercontent.com/jbrooksuk/JSON-Airports/refs/heads/master/airports.json'

DB_CONFIG={
    'host': 'localhost',
    'port': 5433,
    'dbname': 'm_db',
    'user': 'matvei',
    'password': '1234mm',
}

def get_data(url):
    r = req.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        raise ValueError(f"Ожидался список словарей, получено: {type(data).__name__}")
    return data

def pg_type(series):
    value = infer_dtype(series.dropna(), skipna=False)
    if value == 'boolean':
        return 'BOOLEAN'
    if value == 'integer':
        return 'BIGINT'
    if value in ('floating', 'mixed-integer-float'):
        return 'DOUBLE PRECISION'
    return 'TEXT'

def build_dataframe(data):
    df = pd.DataFrame(data)
    for col in ['lat', 'lon']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def df_to_rows(df):
    return df.astype(object).where(df.notna(), None).values.tolist()

def save_records(conn, table, df, key):
    columns = list(df.columns)
    df = df.drop_duplicates(subset=key)

    col_def = [
        sql.SQL('{} {}').
        format(sql.Identifier(col), sql.SQL(pg_type(df[col]))) for col in columns
    ]

    col_def.append(sql.SQL('PRIMARY KEY ({})').format(sql.Identifier(key)))

    create_query = (sql.SQL(
        'CREATE TABLE IF NOT EXISTS {} ({})').
                    format(sql.Identifier(table), sql.SQL(', ').join(col_def)
    ))

    insert_query = (sql.SQL(
        'INSERT INTO {} ({}) VALUES ({}) '
        'ON CONFLICT ({}) DO NOTHING').
                    format(sql.Identifier(table),
                    sql.SQL(', ').join(map(sql.Identifier, columns)),
                    sql.SQL(', ').join([sql.Placeholder()] * len(columns)),
                    sql.Identifier(key),
    ))
    with conn.cursor() as cur:
        cur.execute(create_query)
        cur.executemany(insert_query, df_to_rows(df))

def connect_db():
    return ps.connect(**DB_CONFIG)
def main():
    try:
        data = get_data(URL_API)
        df = build_dataframe(data)

        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT version();')
                print(cur.fetchone()[0])
            save_records(conn, 'airports', df, key='iata')

            with conn.cursor() as cur:
                cur.execute('SELECT count(*) FROM airports;')
                print('Строк в таблице', cur.fetchone()[0])
    except Exception:
        traceback.print_exc()
if __name__ == '__main__':
    main()

