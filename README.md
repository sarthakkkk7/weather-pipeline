# 🌦️Weather Pipeline

A production-style ETL pipeline that fetches real-time weather data, transforms it, and stores it in PostgreSQL — orchestrated with Apache Airflow and containerised with Docker.

Built as part of a hands-on data engineering learning journey.

---

## What it does

Every day, this pipeline automatically:

1. **Extracts** live weather data for Mumbai from the [wttr.in](https://wttr.in) API
2. **Transforms** the raw response — cleans types, adds Fahrenheit conversion
3. **Loads** the result into a PostgreSQL table with upsert logic so re-runs never create duplicates

---

## Tech stack

| Tool | Role |
|------|------|
| Apache Airflow 2.8 | Orchestration & scheduling |
| PostgreSQL 15 | Data storage |
| Python 3.8 | Pipeline logic |
| Docker & Docker Compose | Local containerised environment |
| psycopg2 | Python → Postgres connector |

---

## Project structure

```
weather-pipeline/
├── dags/
│   └── weather_dag.py      # The ETL pipeline — extract, transform, load
├── docker-compose.yml      # Spins up Airflow + Postgres
├── .gitignore
└── README.md
```

---

## Pipeline architecture

```
wttr.in API
    │
    ▼
[ extract_weather ]
  Fetches current conditions for Mumbai
    │
    ▼
[ transform_weather ]
  Converts types, adds °F, normalises fields
    │
    ▼
[ load_weather ]
  Upserts into PostgreSQL
  (one row per city per day — no duplicates)
```

---

## Key concepts demonstrated

**Idempotency** — Running the pipeline multiple times on the same day always results in exactly one row per city. Achieved using PostgreSQL's `ON CONFLICT ... DO UPDATE` (upsert).

**XCom** — Airflow's built-in mechanism for passing data between tasks. Each task pulls the output of the previous one using `context['ti'].xcom_pull()`.

**Retry logic** — Each task is configured to retry once with a 2-minute delay if it fails, mimicking real production behaviour.

**Containerisation** — The entire stack (Airflow webserver, scheduler, and Postgres) runs in Docker, meaning zero local installation beyond Docker Desktop.

---

## Getting started

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

### Run locally

```bash
# 1. Clone the repo
git clone https://github.com/sarthakkkk7/weather-pipeline.git
cd weather-pipeline

# 2. Create required folders
mkdir logs plugins

# 3. Initialise the Airflow database
docker compose up airflow-init

# 4. Start all services
docker compose up -d

# 5. Create an Airflow admin user
docker compose run --rm airflow-webserver airflow users create \
  --username admin --password admin \
  --firstname Admin --lastname User \
  --role Admin --email admin@example.com
```

### Open the Airflow UI

```
http://localhost:8081
```

Login with `admin` / `admin`, enable the `weather_pipeline` DAG, and trigger it manually.

---

## Verify data in Postgres

```bash
docker exec -it weather-pipeline-postgres-1 psql -U airflow -d airflow
```

```sql
SELECT * FROM weather;
```

You should see one row per day with city, temperature (°C and °F), humidity, and weather description.

---

## Sample output

| id | city | temp_c | temp_f | feels_like_c | humidity | description | fetched_at |
|----|------|--------|--------|--------------|----------|-------------|------------|
| 1 | Mumbai | 28.0 | 82.4 | 33.0 | 74 | Haze | 2026-04-07 20:34:19 |

---

## What's next

- [ ] Add support for multiple cities
- [ ] Email alerts on task failure
- [ ] dbt models for data transformation layer
- [ ] Extend to a cloud data warehouse (Snowflake / BigQuery)

---

## 👨‍💻 Author

**Sarthak Satish Deshmukh**   
[GitHub](https://github.com/sarthakkkk7) • [LinkedIn](https://www.linkedin.com/in/sarthakkkk7)

