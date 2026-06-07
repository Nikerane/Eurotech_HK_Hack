# urdf-ops

The training-operations workspace. It was split out of urdf-studio so the
training and perception work has its own home.

It does two jobs:

1. **Perception**: pulls keypoints out of datasets and validates them against a
   stable contract (`urdf-ops.keypoint-observations.v1`).
2. **Training**: runs, monitors, and cancels policy training jobs through
   `/training/*` endpoints.

In the real -> sim -> train -> real loop, urdf-ops is the train + perceive side.
urdf-studio rigs the world, then launches urdf-ops as a sibling to train on it.

Origin repo: https://github.com/amtellezfernandez/urdf-ops

## What is inside

- `backend/` — a FastAPI app (`backend/app.py`). It mounts two routers:
  the training router (`/training`) and the keypoint-observations router
  (`/keypoint-observations`). It also serves `GET /health`.
- `web/` — the Vite + React frontend (Three.js, React Flow, Tailwind).
- `config/` — Vite, ESLint, and TypeScript config.
- `tools/scripts/` — `start-ops.js` (the `npm run start` launcher),
  `setup.js`, and `cli.js`.

## How to run it

You need Node (for the UI) and Python with uvicorn + FastAPI (for the API).

### Run everything at once

```bash
npm install
npm run start
```

`npm run start` runs `tools/scripts/start-ops.js`, which spawns both processes:

- the API: `uvicorn backend.app:app` on port `8001`
- the UI: `vite` on port `5174`

If `.venv-lerobot/bin/python3` exists, the launcher uses that Python. Otherwise
it falls back to plain `python3`. Run `npm run setup` first if you need the venv.

### Run the UI and backend separately

```bash
npm run backend   # uvicorn backend.app:app on 127.0.0.1:8001
npm run dev       # vite UI on 127.0.0.1:5174
```

### Default ports

| Process  | URL                     |
| -------- | ----------------------- |
| Frontend | http://127.0.0.1:5174   |
| API      | http://127.0.0.1:8001   |

The frontend proxies `/api` to the backend at `http://127.0.0.1:8001` (the
`/api` prefix is stripped before forwarding). You can override ports and URLs
with `URDF_OPS_WEB_PORT`, `URDF_OPS_API_PORT`, and `URDF_OPS_BACKEND_URL`.

## Keypoint observations contract

urdf-ops owns dataset/perception keypoint extraction and validation. Downstream
tools (URDF repair, SysID) consume this stable contract instead of writing their
own camera-specific code.

- **Schema version**: `urdf-ops.keypoint-observations.v1`
- **Validate a batch**: `POST /keypoint-observations/validate`
- **Get the schema id**: `GET /keypoint-observations/schema`
  (returns `{"schema_version": "urdf-ops.keypoint-observations.v1"}`)

Both endpoints require simulator-operator access.

### What a frame observation contains

A batch (`KeypointObservationBatch`) carries `schema_version`, optional
`source_dataset_repo`, `source_dataset_revision`, and `robot_id`, plus one or
more frame observations.

Each frame observation (`KeypointFrameObservation`) has:

- `episode_index` (>= 0)
- `frame_index` (>= 0)
- `timestamp_seconds` (optional)
- `camera_name` (optional)
- `keypoints` — one or more keypoint samples

Each keypoint sample (`KeypointObservationSample`) must include:

- `label` (non-empty)
- `confidence` (0.0 to 1.0)
- `frame_id` (defaults to a base frame id)
- `link_name` (optional)
- **and at least one of** `pixel_xy` (2D) or `position_xyz_m` (3D)

A sample with neither `pixel_xy` nor `position_xyz_m` is rejected.

### Validation response

`POST /keypoint-observations/validate` returns `{ valid, summary }`. The summary
is a deterministic coverage report: counts of observations, keypoints, position
keypoints, pixel keypoints, episodes, and frames, plus sorted lists of `labels`,
`link_names`, and `camera_names`.

It also returns `ready_for_geometry_repair`. This is `true` only when the batch
has at least one keypoint with `position_xyz_m`. Warnings are added when no
position keypoints are present, or when no keypoint includes a `link_name`
(without `link_name`, downstream URDF link attribution is unavailable).

URDF repair consumers use `position_xyz_m` plus `link_name` for link-space
calibration.

## How it relates to urdf-studio

urdf-ops was split out of urdf-studio. urdf-studio can launch this repo as a
sibling checkout during its own `npm run start`, so studio handles rigging the
world and urdf-ops handles perception + training. The keypoint contract is the
stable boundary between them: studio (and other consumers) read the validated
`v1` observations instead of embedding camera logic.
