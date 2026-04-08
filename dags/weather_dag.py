from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import psycopg2

default_args = {
    'owner': 'sarthak',
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

# Postgres connection details — pointing to our Docker container
DB_CONFIG = {
    'host':     'postgres',   # container name = hostname inside Docker
    'port':      5432,
    'dbname':   'airflow',
    'user':     'airflow',
    'password': 'airflow',
}

with DAG(
    dag_id='weather_pipeline',
    default_args=default_args,
    description='Fetch Mumbai weather daily',
    schedule='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['weather', 'beginner'],
) as dag:

    def extract_weather():
        url = "https://wttr.in/Mumbai?format=j1"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        current = data['current_condition'][0]
        result = {
            'city':         'Mumbai',
            'temp_c':       current['temp_C'],
            'feels_like_c': current['FeelsLikeC'],
            'humidity':     current['humidity'],
            'description':  current['weatherDesc'][0]['value'],
            'fetched_at':   datetime.now().isoformat(),
        }
        print(f"Extracted: {result}")
        return result

    def transform_weather(**context):
        raw = context['ti'].xcom_pull(task_ids='extract_weather')
        raw['temp_c']       = float(raw['temp_c'])
        raw['feels_like_c'] = float(raw['feels_like_c'])
        raw['temp_f']       = round(raw['temp_c'] * 9/5 + 32, 1)
        raw['humidity']     = int(raw['humidity'])
        print(f"Transformed: {raw}")
        return raw

    def load_weather(**context):
        data = context['ti'].xcom_pull(task_ids='transform_weather')

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
            data['fetched_at'][:10],   # "2026-04-07T20:34:19..." → "2026-04-07"
        ))

        conn.commit()
        cur.close()
        conn.close()
        print(f"Loaded: {data['city']} | {data['temp_c']}C / {data['temp_f']}F | {data['description']}")

    t1 = PythonOperator(task_id='extract_weather',   python_callable=extract_weather)
    t2 = PythonOperator(task_id='transform_weather', python_callable=transform_weather)
    t3 = PythonOperator(task_id='load_weather',      python_callable=load_weather)

    t1 >> t2 >> t3