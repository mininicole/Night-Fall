# ============================================================
# Night Fall — Production Dockerfile
#
# Fetches Ombre Brain at build time via git clone.
# No Ombre source code lives in the Night Fall repository.
#
# Build:
#   docker build \
#     --build-arg OMBRE_REPO=https://github.com/P0luz/Ombre-Brain.git \
#     -t night-fall .
#
# Run:
#   docker run -e OMBRE_API_KEY=sk-xxx -p 8000:8000 night-fall
# ============================================================

FROM python:3.12-slim

# ── Build args ────────────────────────────────────────────────────────────────
# Point OMBRE_REPO at your own Ombre fork if needed.
ARG OMBRE_REPO=https://github.com/P0luz/Ombre-Brain.git
ARG OMBRE_BRANCH=main

# ── System deps ───────────────────────────────────────────────────────────────
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# ── Fetch Ombre at build time ─────────────────────────────────────────────────
RUN git clone --depth 1 --branch ${OMBRE_BRANCH} ${OMBRE_REPO} /ombre \
    && cp /ombre/config.example.yaml /ombre/config.yaml
RUN pip install --no-cache-dir -r /ombre/requirements.txt

# ── Install Night Fall ────────────────────────────────────────────────────────
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .

# ── Runtime config ────────────────────────────────────────────────────────────
ENV OMBRE_HOME=/ombre
ENV OMBRE_TRANSPORT=streamable-http
ENV OMBRE_PORT=8000
ENV OMBRE_BUCKETS_DIR=/app/data/buckets
ENV NIGHT_FALL_DATA_DIR=/app/data/night_fall

# Single persistent volume for both Ombre buckets and Night Fall dreams.
VOLUME ["/app/data"]
EXPOSE 8000

CMD ["python", "-m", "night_fall.launcher"]
