# Distributed Database Project Report Template

## 1. Project Overview

Describe the goal of the system:

- Build a simple e-commerce web app
- Connect it to MongoDB
- Demonstrate distributed database ideas
- Show replication, failover, and recovery

## 2. Technologies Used

- FastAPI
- MongoDB
- HTML / CSS / JavaScript
- Docker Compose

## 3. System Architecture

Explain the architecture in simple words:

- The frontend sends requests to FastAPI
- FastAPI uses a routing layer for products
- MongoDB stores data
- Three MongoDB nodes form a replica set

Suggested screenshots:

- Main web page
- Replica set status in the UI
- MongoDB containers running

## 4. Distributed Database Concepts

### Sharding Simulation

Explain:

- Products are routed using `product_id % 2`
- Odd and even product IDs are stored in different logical shards
- This simulates request routing in a distributed system

### Replication

Explain:

- The project uses 3 MongoDB nodes in one replica set
- One node acts as primary
- Other nodes act as secondary replicas
- Writes go to the primary and replicate to secondaries

## 5. CRUD Operations Demonstrated

- Create product
- List products
- Create cart
- Add to cart
- Place order

Include screenshots of each operation.

## 6. Failover and Recovery

Suggested demo steps:

1. Open the cluster status section in the web UI.
2. Stop the primary node using Docker.
3. Wait for a new primary election.
4. Refresh the cluster status.
5. Show that the application reconnects to the new primary.
6. Restart the stopped node and show recovery.

Suggested commands:

```powershell
docker stop mongo1
docker start mongo1
```

Note:

- If `mongo1` is not the primary at the time, stop whichever node is primary.

## 7. Conclusion

Summarize what the team learned:

- How distributed database routing works
- How MongoDB replica sets support replication
- How failover improves availability

