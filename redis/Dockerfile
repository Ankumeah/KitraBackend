FROM redis:alpine

COPY . /opt/redis/
RUN chmod +x /opt/redis/run_redis.sh

ENTRYPOINT [ "/opt/redis/run_redis.sh" ]
