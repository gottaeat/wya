# wya
wya is an ip asn and geolocation lookup tool built with flask and geolite2
databases. it dumps out a json that is similar to ipinfo.io, with additional ptr
record validation.

```sh
# get a pong
$ curl https://ip.example.com/ping
PONG

# query a specific public ip
$ curl https://ip.example.com/`dig +short facebook.com`
{
  "ip": "157.240.253.35",
  "asn": "AS32934",
  "org": "FACEBOOK",
  "hostname": [
    {
      "edge-star-mini-shv-02-fra5.facebook.com.": {
        "resolves_back": true
      }
    }
  ],
  "country": "DE",
  "city": "Frankfurt am Main",
  "region": "Hesse",
  "loc": "50.1187,8.6842",
  "tz": "Europe/Berlin"
}

# query your own ip
$ curl https://ip.example.com
{
  "ip": "93.184.215.14",
  "asn": "AS15133",
  "org": "EDGECAST",
  "hostname": null,
  "country": "US",
  "city": null,
  "region": null,
  "loc": "37.751,-97.822",
  "tz": "America/Chicago"
}
```

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

wya takes a `SIGHUP` to reload the databases without service interruption.

## example reverse proxy setup
```nginx
server {
    listen 80;
    server_name ip.example.com;

    return 301 https://$host:443$request_uri;
}

server {
    listen 443 ssl;
    server_name ip.example.com;

    location / {
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
