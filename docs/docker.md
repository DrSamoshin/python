docker compose -f docker/docker-compose.dev.yml up -d
docker exec -it myapp_postgres_dev psql -U dev_user -d myapp_dev