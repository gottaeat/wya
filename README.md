# wya
wya is an ip asn and geolocation lookup tool built with flask. it dumps out a
json that is similar to ipinfo.io, with ptr record validation.

## installation
```sh
# 1. get the compose file
mkdir wya/; cd wya/
curl -LO \
    https://raw.githubusercontent.com/gottaeat/wya/master/docker-compose.yml

# 2. create the volume mount for geolite2 databases
mkdir data/
for i in ASN City; do
    curl -Lo ./data/GeoLite2-${i}.mmdb https://git.io/GeoLite2-${i}.mmdb
done

# 3. docker compose up
docker compose up -d
```

## example reverse proxy setup
wya on its own does not set any kind of limits or restrictions. the following
nginx `http{}` block sets a reverse proxy that limits requests to 2000 per
unique ip.

```nginx
server {
    listen 80;
    server_name ip.example.com;

    return 301 https://$host:443$request_uri;
}

server {
    listen 443 ssl;
    server_name ip.example.com;

    limit_req_zone $binary_remote_addr zone=one:10m rate=2000r/d;

    location / {
        limit_req zone=one burst=10 nodelay;

        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Connection $http_connection;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
