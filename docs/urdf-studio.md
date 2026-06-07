# URDF Studio

A local robotics workbench. It runs on your machine, in the browser, like a Blender for robots.

Use it to:

- Load a URDF robot and look at its joints, links, and scene.
- Edit joints and keyframes.
- Replay LeRobot episodes and inspect them frame by frame.
- Hand off to URDF Ops for training.

In this repo it is the submodule at `urdf-studio/`, the fork
[github.com/Nikerane/urdf-studio](https://github.com/Nikerane/urdf-studio) (branch `hkgenesis`).

## Where it fits in REAL2SIM

The pipeline is: real image -> generated world -> **rig in urdf-studio** -> train via urdf-ops / lerobot -> replay on the real SO-101 arm.

urdf-studio is the rigging and inspection stage. The generated world arrives here, you give it degrees of freedom (joints), and you replay or review episodes before sending the work to training. The training workbench, URDF Ops, opens straight from the top bar.

## Prerequisites

- Node.js and npm
- Python 3
- `uv` (from <https://astral.sh/uv>)

On Linux, native Python deps need build tools:

```bash
sudo apt-get update
sudo apt-get install python3-dev build-essential
```

On macOS, install the Xcode command line tools so native libraries build:

```bash
xcode-select --install
```

Some native parts (teleop, IK daemon) also need Rust. Setup can install Rust for you when the configured runtime needs it.

## Setup

Run once:

```bash
cd urdf-studio
npm run setup
```

Setup installs:

- npm dependencies for URDF Studio
- the Python environment at `.venv-lerobot`
- backend, LeRobot, hardware, and simulation dependencies
- the local `i-love-urdf` CLI (available as `npx ilu`)
- the sibling URDF Ops checkout at `../urdf-ops`

Useful flags and env vars:

```bash
URDF_OPS_ROOT=/path/to/urdf-ops npm run setup   # point at an existing urdf-ops
URDF_STUDIO_SKIP_URDF_OPS_SETUP=1 npm run setup # skip the urdf-ops step
npm run setup -- --install-global-ilu           # put ilu on your PATH
npm run setup -- --twin                          # add VGGT "twin" deps
```

On macOS, setup skips the Placo/Pinocchio collision stack by default (the pinned native libs are not reliably relocatable). Force it only if you need OpenArm self-collision checks:

```bash
URDF_STUDIO_INSTALL_COLLISION_STACK=1 npm run setup
```

If URDF Ops dependencies already exist, setup skips the install and prints `URDF Ops dependencies already installed`.

## Run modes

Use `npm run start` for normal work. The others are for specific cases.

> **In this repo, point Studio at urdf-ops.** Studio looks for the training
> workspace at the sibling `../urdf-ops`, but that lookup may not resolve here.
> Pass the path explicitly:
>
> ```bash
> cd urdf-studio
> URDF_OPS_ROOT="$(pwd)/../urdf-ops" npm run start
> ```
>
> An absolute path works too, e.g. `URDF_OPS_ROOT=/Users/you/Eurotech_HK_Hack/urdf-ops npm run start`.

| Command | Use for | Starts backend? | Starts URDF Ops? |
| --- | --- | --- | --- |
| `npm run start` | Normal local app | Yes | Yes, or reuses it |
| `npm run dev` | Frontend-only UI work | No | No |
| `npm run team` | Sharing on same Wi-Fi / Tailnet | Yes | Yes, or reuses it |
| `npm run data` | Phone / tunnel data mode | Yes | Yes, plus restricted public ingress |
| `npm run start -- --help` | See runtime options | - | - |

`npm run dev` is frontend only. Backend calls like `/api/version`, `/api/ik/config`, and `/robot-mastering/*` will fail there. That is expected. Use `npm run start` for the full product.

## Ports

A healthy `npm run start` opens four local services and prints a `Ready:` block.

| Service | URL |
| --- | --- |
| Studio frontend | http://127.0.0.1:5173 |
| Studio backend | http://127.0.0.1:8000 |
| URDF Ops frontend | http://127.0.0.1:5174 |
| URDF Ops backend | http://127.0.0.1:8001 |

By default everything binds to loopback (your machine only).

## Smoke test

1. Open http://127.0.0.1:5173.
2. Click `Play Sample Motion`. Wait for `lekiwi.urdf loaded`.
3. In the `Episodes` panel, click the first episode's play button once.
4. Confirm: the button changes to pause, the frame counter advances, the robot moves, and the graph cursor moves smoothly.

If this works, the viewer, dataset replay, graph overlay, and full stack are all healthy.

Backend health checks:

```bash
curl http://127.0.0.1:8000/health   # studio backend, expect {"status":"ok","yourdfpy":true}
curl http://127.0.0.1:8001/health   # ops backend, expect {"status":"ok"}
```

## Common workflows

### Load the sample motion

1. Start with `npm run start`.
2. Click `Play Sample Motion`.
3. Use the `Episodes` panel to replay the sample trajectories.

### Load your own robot

1. On the first screen, use the `Robot` loader.
2. Drop a URDF/Xacro folder, a zip, or the files plus meshes.
3. Include meshes (`.stl`, `.glb`, `.gltf`, `.obj`, `.dae`) when the URDF references them.
4. Check the scene tree and joints panel after load.
5. Use `Reset Pose`, the joint controls, and the replay tools to inspect behavior.

Note: editing a URDF file on disk does not show up on refresh. Studio caches the parsed robot scene. To pick up URDF changes, do a full robot re-import (or clear site data in DevTools).

### Replay or review episodes

1. Load a dataset or the sample motion.
2. Pick an episode in the left `Episodes` list.
3. Choose the replay zero mode: `Target` (loaded robot zero pose) or `Raw` (dataset visualizer convention).
4. Use the inline episode graph to inspect frame, time, joint curves, and velocity/limit markers.
5. Play one episode and watch the robot and graph stay in sync.

### Open the training tools (URDF Ops)

Click `URDF Ops` in the top bar. Studio opens or reuses the synchronized session at http://127.0.0.1:5174. URDF Ops is the sibling checkout at `../urdf-ops` by default; override it with `URDF_OPS_ROOT=/path/to/urdf-ops npm run start`.

## Workspace map

- **Top bar**: action menus (`File`, `Utils`, `Worlds`, `View`, `Dataset`, `Create`, `IK`), the `URDF Ops` button, `Sim Prep Review`, and `Cams` / `Leader` / `Follower` for cameras and teleoperation.
- **Left sidebar**: `Record`, FPS controls, dataset policy, `Playback`, and the `Episodes` list (replay, retake, export, delete, reorder).
- **Center viewer**: the 3D robot/world view, gizmos, scene objects, and `Reset Pose`.
- **Episode graph**: frame/time, effective FPS, selected signals, replay cursor, and velocity/limit markers. Edit mode exposes timeline and joint-curve editing.
- **Right sidebar**: scene hierarchy, joint/link/object tabs, selection details, and live joint values.

## Troubleshooting

### UI opens but API calls fail (500s)

You probably started frontend-only mode (`npm run dev`). Stop it and run the full stack:

```bash
npm run start
curl http://127.0.0.1:8000/health
```

### Port already in use

Pick explicit ports:

```bash
npm run start -- --web-port 3001 --api-port 9001
URDF_OPS_WEB_PORT=5176 URDF_OPS_API_PORT=8003 npm run start
```

If ports are stuck after a crash, free them:

```bash
lsof -nP -iTCP:8000 -iTCP:8001 -iTCP:5173 -iTCP:5174 -sTCP:LISTEN -t | xargs kill
```

### Setup looks frozen at "Setting up URDF Ops workspace"

That step manages `../urdf-ops`. If its dependencies are missing, the npm install can take a while; setup streams the output. To skip it for now:

```bash
URDF_STUDIO_SKIP_URDF_OPS_SETUP=1 npm run setup
```

### URDF Ops does not open

Check both Ops services, then override ports if they are busy:

```bash
curl http://127.0.0.1:8001/health
curl -I http://127.0.0.1:5174
URDF_OPS_WEB_PORT=5176 URDF_OPS_API_PORT=8003 npm run start
```

### "URDF Studio could not load" on first open (Vite warm-up race)

Clear the Vite cache, restart, and open a fresh tab (do not reuse a `?urdfStudioBootRetry=...` URL):

```bash
rm -rf node_modules/.vite web/node_modules/.vite
npm run start
```

### `i-love-urdf` module not found, robot-mastering returns 500

The robot-mastering runner expects a sibling `../i-love-urdf` directory. The code it needs is already installed as the npm package. Symlink the sibling path to it:

```bash
ln -s urdf-studio/node_modules/i-love-urdf i-love-urdf
```

The backend spawns a fresh subprocess per request, so this takes effect immediately. The symlink is untracked by git; recreate it after a fresh clone.

### Real robot not detected, "Failed to fetch" in Leader Input

Two common causes:

1. **Stale servers on the backend ports.** A leftover process holding 8000/8001 returns errors with no CORS headers, which the browser reports as "Failed to fetch". Find and kill it:

   ```bash
   lsof -nP -iTCP:8000 -iTCP:8001 -sTCP:LISTEN
   kill <pid> <pid>
   ```

2. **`lerobot` missing from the Studio venv.** The backend probes motors with `lerobot` inside its own `.venv-lerobot`. macOS setup skips it by default, so detection finds the serial devices but reports `No module named 'lerobot'` and zero motors. Install it (pulls torch + Feetech SDK, a few GB):

   ```bash
   uv pip install --python .venv-lerobot/bin/python3 'lerobot[feetech]'
   # or re-run setup with URDF_STUDIO_INSTALL_LEROBOT=1
   ```

   Then restart `npm run start` and use Leader Input -> Rescan.

   Serial ports are exclusive: only one program can own a `/dev/tty.usbmodem*` device at a time. Let Studio own the leader and follower ports, and do not run `lerobot-teleoperate` at the same time.

## Developer checks

```bash
npm run lint
npm run typecheck
npm run test
npm run build
npm run test:backend
```

Run a single test:

```bash
npm run test -- web/src/features/dataset/episode-viewer/modalHelpers.test.ts
npm run test:backend -- backend/tests/test_datasets_service.py
```
