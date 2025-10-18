docker compose -f docker/docker-compose.dev.yml up -d
docker exec -it myapp_postgres_dev psql -U dev_user -d myapp_dev

docker compose -f docker/docker-compose.test.yml up -d
docker exec -it myapp_postgres_test psql -U test_user -d myapp_test

psql -U postgres -f init_db.sql

docker exec -it myapp_redis_dev redis-cli
docker exec -it myapp_redis_test redis-cli

 docker logs myapp_redis_dev
 docker logs myapp_redis_test