FROM python:3.11-alpine AS wya

RUN \
    addgroup -g 1337 wya && \
    adduser -D -H -G wya -u 1337 wya

COPY . /repo

RUN pip install /repo

EXPOSE 8080/tcp
CMD ["/repo/docker/entrypoint.sh"]
