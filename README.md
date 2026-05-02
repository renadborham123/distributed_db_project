# Distributed Database Project

This project is a simple student-friendly distributed e-commerce system built with:

- FastAPI
- MongoDB
- HTML, CSS, JavaScript

It is designed to demonstrate two distributed database ideas without making the
project too complex:

1. **Sharding simulation in the application layer**
2. **Replication using a real 3-node MongoDB replica set**

## Features

- Create product
- List products
- Create cart
- Add to cart
- Place order
- View replica set status from the frontend

## How the distributed part works

### 1. Sharding simulation

The application simulates sharding by using two logical MongoDB shard databases:

- `ecommerce_shard_0`
- `ecommerce_shard_1`

The routing layer decides where a product should be stored:

```python
shard_number = product_id % 2
```

This means:

- Even product IDs are routed to `shard_0`
- Odd product IDs are routed to `shard_1`

Why this matters:

- In a distributed system, the app needs routing logic
- The router makes sure reads and writes go to the correct node
- Logs show which shard is used for each product request

### 2. Replication

The project also supports a real 3-node MongoDB replica set:

- `mongo1`
- `mongo2`
- `mongo3`

With the replica set:

- One node becomes **primary**
- Two nodes become **secondary**
- Writes go to the primary
- Data is replicated to the secondaries
- If the primary fails, MongoDB elects a new primary

## Project structure

```text
backend/
  main.py
  db_router.py
  models.py
frontend/
  index.html
  script.js
  style.css
mongo/
  init-replica.js
scripts/
  setup_replica_set.ps1
docker-compose.yml
REPORT_TEMPLATE.md
```

## Option A: Run with one local MongoDB instance

This is the fastest way to test the web app and the sharding simulation.

1. Start MongoDB on `localhost:27017`
2. Install Python packages:

```bash
pip install -r requirements.txt
```

3. Start the app:

```bash
uvicorn backend.main:app --reload
```

4. Open:

```text
http://127.0.0.1:8000
```

In this mode:

- Sharding simulation works
- Replica set status will show a helpful message saying replication is not active

## Option B: Run with a 3-node replica set

This is the best option for the full assignment because it demonstrates
replication, failover, and recovery.

### Prerequisites

- Docker Desktop
- Python installed

### Steps

1. Start and initialize the replica set:

```powershell
.\scripts\setup_replica_set.ps1
```

2. Set the MongoDB connection string:

```powershell
$env:MONGODB_URL="mongodb://localhost:27017,localhost:27018,localhost:27019/?replicaSet=rs0"
```

3. Install dependencies:

```powershell
pip install -r requirements.txt
```

4. Start the FastAPI app:

```powershell
uvicorn backend.main:app --reload
```

5. Open:

```text
http://127.0.0.1:8000
```

6. In the web app, check the **Replica Set Status** section.

## Failover demo

After the replica set is running:

1. Open the app and refresh the cluster status
2. Identify the primary node
3. Stop the primary container:

```powershell
docker stop mongo1
```

4. Wait a few seconds
5. Refresh the cluster status again
6. MongoDB should elect a new primary
7. Start the stopped node again:

```powershell
docker start mongo1
```

This demonstrates failover and recovery.

Note:

- If `mongo1` is not the current primary, stop the node that is primary instead.

## Main API endpoints

- `POST /products`
- `GET /products`
- `POST /carts`
- `GET /carts/{cart_id}`
- `POST /carts/{cart_id}/items`
- `POST /orders/{cart_id}`
- `GET /cluster/status`
