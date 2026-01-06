#! /bin/sh

sed -i "s/REDIS_SESSION_USER_USERNAME/${REDIS_SESSION_USER_USERNAME}/g" /opt/redis/redis.conf
sed -i "s/REDIS_SESSION_USER_PASSWORD/${REDIS_SESSION_USER_PASSWORD}/g" /opt/redis/redis.conf

sed -i "s/REDIS_REFRESH_USER_USERNAME/${REDIS_REFRESH_USER_USERNAME}/g" /opt/redis/redis.conf
sed -i "s/REDIS_REFRESH_USER_PASSWORD/${REDIS_REFRESH_USER_PASSWORD}/g" /opt/redis/redis.conf

exec redis-server /opt/redis/redis.conf
