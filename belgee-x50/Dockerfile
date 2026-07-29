FROM alpine:3.22

RUN apk add --no-cache bash jq python3 py3-aiohttp

WORKDIR /app
COPY app /app
RUN chmod +x /app/run.sh

ENTRYPOINT ["/app/run.sh"]
