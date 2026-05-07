# 🌦️Weather Pipeline 

A production-style ETL pipeline that fetches real-time weather data, transforms it, and stores it in PostgreSQL — orchestrated with Apache Airflow and containerised with Docker.

Built as part of a hands-on data engineering learning journey.

---

## What it does -

Every day, this pipeline automatically:

1. **Extracts** live weather data for Mumbai, Pune, Delhi & Bengaluru from the [wttr.in](https://wttr.in) API
2. **Transforms** the raw response — cleans types, adds Fahrenheit conversion
3. **Loads** the result into a PostgreSQL table with upsert logic so re-runs never create duplicates

---

## Tech stack -

| Tool | Role |
|------|------|
| Apache Airflow 2.8 | Orchestration & scheduling |
| PostgreSQL 18.2 | Data storage |
| Python 3.13 | Pipeline logic |
| Docker & Docker Compose | Local containerised environment |
| psycopg2 | Python → Postgres connector |

---

## Project structure -

```
weather-pipeline/
├── dags/
│   └── weather_dag.py      # The ETL pipeline — extract, transform, load
├── docker-compose.yml      # Spins up Airflow + Postgres
├── .gitignore
└── README.md
```

---

## Pipeline architecture -

<img width="1000" height="300" alt="architecture" src="https://github.com/user-attachments/assets/97e7b226-e51e-444b-b9ec-0ce1a3582f95" />



---

## Key concepts demonstrated -

**Idempotency** — Running the pipeline multiple times on the same day always results in exactly one row per city. Achieved using PostgreSQL's `ON CONFLICT ... DO UPDATE` (upsert).

**XCom** — Airflow's built-in mechanism for passing data between tasks. Each task pulls the output of the previous one using `context['ti'].xcom_pull()`.

**Retry logic** — Each task is configured to retry once with a 2-minute delay if it fails, mimicking real production behaviour.

**Containerisation** — The entire stack (Airflow webserver, scheduler, and Postgres) runs in Docker, meaning zero local installation beyond Docker Desktop.

---

## Getting started -

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

## Screenshots from Airflow -

### Airflow DAG — successful run
<img width="1000" height="300" alt="image" src="https://github.com/user-attachments/assets/35c33d41-9f00-4702-a078-7f0845d9061d" />


### Pipeline runs history
<img width="1000" height="300" alt="image" src="https://github.com/user-attachments/assets/8205f9a7-6e5f-4ffa-90ff-db116a436520" />


---

## Verify data in Postgres -

```bash
docker exec -it weather-pipeline-postgres-1 psql -U airflow -d airflow
```
```sql
SQL
--This query is for unordered result
SELECT * FROM weather;
```
```sql
SQL
--This query is for alphabetically ordered result
SELECT city, temp_c, temp_f, description, fetch_date
FROM weather
ORDER BY city;
```

You should see one row per day with city, temperature (°C and °F), humidity, and weather description.

---

## Sample output -

<img width="1000" height="300" alt="image" src="https://github.com/user-attachments/assets/946b8a94-f6d9-4e64-8922-739b1ea724f8" />



> Note: Mumbai has extra records from the one city version of this DAG pipeline, which was letter upgraded to support multiple cities.

---

## What's next -

- [x] Add support for multiple cities
- [ ] Email alerts on task failure
- [ ] dbt models for data transformation layer
- [ ] Extend to a cloud data warehouse (Snowflake / BigQuery)

---

## 👨‍💻 Author -

**Sarthak Satish Deshmukh**   
[GitHub](https://github.com/sarthakkkk7) • [LinkedIn](https://www.linkedin.com/in/sarthakkkk7)

