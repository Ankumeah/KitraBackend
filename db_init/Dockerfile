FROM alpine

WORKDIR /opt/db_init/

COPY . .

RUN apk add --no-cache postgresql-client
RUN chmod +x ./db_init.sh

ENTRYPOINT [ "./db_init.sh" ]
