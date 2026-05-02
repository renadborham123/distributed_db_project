$ErrorActionPreference = "Stop"

Write-Host "Starting MongoDB containers..."
docker compose up -d

Write-Host "Waiting for mongod processes to start..."
Start-Sleep -Seconds 8

$statusCommand = "try { rs.status().ok } catch (e) { 0 }"
$status = docker exec mongo1 mongosh --quiet --eval $statusCommand

if ($status -eq "1") {
    Write-Host "Replica set is already initialized."
    exit 0
}

Write-Host "Initializing replica set..."
docker cp ".\mongo\init-replica.js" "mongo1:/init-replica.js"
docker exec mongo1 mongosh /init-replica.js

Write-Host "Replica set initialized."
Write-Host "Use this connection string in the app:"
Write-Host 'mongodb://localhost:27017,localhost:27018,localhost:27019/?replicaSet=rs0'

