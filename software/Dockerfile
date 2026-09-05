FROM python:3.12-slim
WORKDIR /app/software
COPY lingban ./lingban
COPY web ./web
RUN mkdir data && chown -R 10001:10001 /app
USER 10001:10001
VOLUME ["/app/software/data"]
# Bind all interfaces only inside container; publish host port explicitly on 127.0.0.1.
CMD ["python", "-m", "lingban.server", "--host", "0.0.0.0", "--allow-network"]
