from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import psycopg2
import os

default_args = {
    'owner': 'sarthak',
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

DB_CONFIG = {
    'host':     'postgres',
    'port':      5432,
    'dbname':   'airflow',
    'user':     'airflow',
    'password': 'airflow',
}

# --- Add or remove cities here anytime ---
CITIES = ['Mumbai', 'Pune', 'Delhi', 'Bangalore']

def extract_weather(city):
    url = f"https://wttr.in/{city}?format=j1"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    current = data['current_condition'][0]
    result = {
        'city':         city,
        'temp_c':       current['temp_C'],
        'feels_like_c': current['FeelsLikeC'],
        'humidity':     current['humidity'],
        'description':  current['weatherDesc'][0]['value'],
        'fetched_at':   datetime.now().isoformat(),
    }
    print(f"Extracted: {result}")
    return result

def transform_weather(city, **context):
    raw = context['ti'].xcom_pull(task_ids=f'extract_{city}')
    raw['temp_c']       = float(raw['temp_c'])
    raw['feels_like_c'] = float(raw['feels_like_c'])
    raw['temp_f']       = round(raw['temp_c'] * 9/5 + 32, 1)
    raw['humidity']     = int(raw['humidity'])
    print(f"Transformed: {raw}")
    return raw

def load_weather(city, **context):
    data = context['ti'].xcom_pull(task_ids=f'transform_{city}')

    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS weather (
            id           SERIAL PRIMARY KEY,
            city         TEXT,
            temp_c       REAL,
            temp_f       REAL,
            feels_like_c REAL,
            humidity     INTEGER,
            description  TEXT,
            fetched_at   TIMESTAMP,
            fetch_date   DATE,
            UNIQUE (city, fetch_date)
        )
    ''')

    cur.execute('''
        INSERT INTO weather
          (city, temp_c, temp_f, feels_like_c, humidity, description, fetched_at, fetch_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (city, fetch_date)
        DO UPDATE SET
          temp_c       = EXCLUDED.temp_c,
          temp_f       = EXCLUDED.temp_f,
          feels_like_c = EXCLUDED.feels_like_c,
          humidity     = EXCLUDED.humidity,
          description  = EXCLUDED.description,
          fetched_at   = EXCLUDED.fetched_at
    ''', (
        data['city'],
        data['temp_c'],
        data['temp_f'],
        data['feels_like_c'],
        data['humidity'],
        data['description'],
        data['fetched_at'],
        data['fetched_at'][:10],
    ))

    conn.commit()
    cur.close()
    conn.close()
    print(f"Loaded: {data['city']} | {data['temp_c']}C / {data['temp_f']}F | {data['description']}")


with DAG(
    dag_id='weather_pipeline',
    default_args=default_args,
    description='Fetch weather for multiple cities daily',
    schedule='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['weather', 'beginner'],
) as dag:

    # --- Dynamically create 3 tasks per city ---
    for city in CITIES:
        t1 = PythonOperator(
            task_id=f'extract_{city}',
            python_callable=extract_weather,
            op_kwargs={'city': city},   # pass city as argument
        )

        t2 = PythonOperator(
            task_id=f'transform_{city}',
            python_callable=transform_weather,
            op_kwargs={'city': city},
        )

        t3 = PythonOperator(
            task_id=f'load_{city}',
            python_callable=load_weather,
            op_kwargs={'city': city},
        )

        t1 >> t2 >> t3   # each city has its own independent chain