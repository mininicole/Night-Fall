# Night Fall

Night Fall is a runtime extension for [Ombre Brain](https://github.com/P0luz/Ombre-Brain). It adds one MCP tool, `night_fall`, to the same Ombre MCP server instance.

Night Fall does not fork, vendor, bundle, or redistribute Ombre. It extends a user-provided Ombre installation at runtime. Existing Ombre tools remain unchanged:

```text
breath / hold / grow / trace / pulse / dream
```

`dream` remains Ombre's original feature. `night_fall` is separate.

## What It Does

`night_fall` creates latent dreams that fade only after repeated failed surfacing:

1. `night_fall(action="generate")` selects emotionally charged Ombre memories, extracts imagery, writes a dream, and stores it privately.
2. The generated dream is not returned immediately. Its `dream_mode` is one of `integrative`, `fragmentary`, or `residual`.
3. For the first 3 hours, it cannot surface.
4. After 3 hours, `night_fall(action="surface")` may return it if the current affect resonates with the dream's `core_affect`.
5. After 24 hours, a very small spontaneous surfacing chance is also allowed.
6. Each surfacing evaluation that does not pick the dream increments `surface_attempts`. A dream is not removed by wall-clock time — it is deleted only after it has been evaluated `MAX_SURFACE_ATTEMPTS` (4) times and still not surfaced.
7. Surfaced dreams are returned through a dedicated channel and do not automatically enter long-term memory. A surfaced dream is preserved only if the user or Claude explicitly performs a hold-like action on it.

## Cloud Deployment (Zeabur / Railway / Render)

Night Fall provides a `Dockerfile` that fetches Ombre Brain at build time via `git clone`. No Ombre source code lives in this repository. The result is a single MCP service exposing all Ombre tools plus `night_fall`.

### How it works

```
docker build (OMBRE_REPO=...) → image contains /ombre + /app
python -m night_fall.launcher → one MCP server at :8000
Claude Desktop → mcp-remote → https://your-host.app/mcp (7 tools)
```

### Deploy to Zeabur

1. Fork this Night Fall repository to your GitHub account.
2. In Zeabur, create a new service and import your forked repository.
3. Zeabur reads `zeabur.json` and builds from `Dockerfile` automatically.
4. Set the following environment variables in the Zeabur dashboard:

   | Variable | Required | Notes |
   |----------|----------|-------|
   | `OMBRE_API_KEY` | ✅ | Your DeepSeek / LLM provider key |
   | `OMBRE_REPO` | optional | Defaults to the upstream Ombre repo; set to your own fork URL if needed |
   | `OMBRE_BRANCH` | optional | Defaults to `main` |
   | `OMBRE_PORT` | optional | Defaults to `8000` |

5. Mount a persistent volume at `/app/data` to preserve bucket data and dreams across restarts.
6. After deployment, update your Claude Desktop config:

   ```json
   "ombre-brain": {
     "command": "npx",
     "args": ["-y", "mcp-remote", "https://your-night-fall.zeabur.app/mcp"]
   }
   ```

   Claude will see all original Ombre tools plus `night_fall` through a single endpoint.

### Railway / Render

The same `Dockerfile` works with Railway and Render. Point them at your forked Night Fall repository and set the same environment variables.

### Build locally with Docker

```bash
docker build \
  --build-arg OMBRE_REPO=https://github.com/P0luz/Ombre-Brain.git \
  -t night-fall .

docker run \
  -e OMBRE_API_KEY=sk-xxxx \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  night-fall
```

---

## Local Python Setup

Install Ombre Brain first. Then download or clone Night Fall anywhere you like. It is convenient during development to place the folders beside each other:

```text
somewhere/
  Ombre-Brain/
  Night-Fall/
```

That sibling layout is only a development convenience. End users do not need to place `Ombre-Brain/` inside or beside `Night-Fall/`.

From the Night Fall folder:

```bash
python scripts/install_local.py
python -m night_fall.launcher
```

The installer asks for your Ombre folder, validates `server.py`, and writes `.nightfall.yaml`.

You can also skip the installer:

```bash
OMBRE_HOME=/absolute/path/to/Ombre-Brain python -m night_fall.launcher
```

Keep using the same Claude MCP server entry you used for Ombre. You should see the original tools plus `night_fall`.

## Docker Setup

Night Fall does not provide a second Ombre image. It reuses Ombre's existing `ombre-brain` service from `docker-compose.user.yml`, bind-mounts this Night Fall folder, and changes the command to start Night Fall's launcher.

If your folders are arranged like this:

```text
somewhere/
  Ombre-Brain/
    docker-compose.user.yml
  Night-Fall/
```

run from `Ombre-Brain/`:

```bash
docker compose -f docker-compose.user.yml -f ../Night-Fall/docker/docker-compose.nightfall.override.yml up -d
```

This keeps the same Ombre container, same data mount, same port, and same Claude MCP config. Night Fall stores extension state in `/data/night_fall` inside the existing Ombre data volume.

If your Night Fall folder is elsewhere, edit only the override file's bind mount path.

## Tool Actions

```text
night_fall(action="generate")
night_fall(action="surface")
night_fall(action="status")
night_fall(action="cleanup")
```

Optional inputs:

```text
current_valence: 0.0-1.0, or -1 when unknown
current_arousal: 0.0-1.0, or -1 when unknown
current_motifs: accepted for interface compatibility; V1 surfacing is affect-led
debug: true/false
```

## Prompt Snippet

Night Fall does not edit Ombre's `CLAUDE_PROMPT.md`. If you want surfaced dreams to appear naturally after startup breath, add the contents of `NIGHT_FALL_PROMPT_APPEND.md` to your own Claude instructions.

## Development Notes

For this workspace, `Night-Fall-dev/Ombre-Brain/` is a read-only Ombre reference copy for source reading and integration tests. Do not edit it. All Night Fall source code lives in `Night-Fall-dev/Night-Fall/`.
