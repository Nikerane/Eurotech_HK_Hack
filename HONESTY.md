# HONESTY.md

Eurotech x HKTE Hackathon — June 5–7, 2026

## What existed before the hackathon

- **urdf-studio** — A local robotics workbench (Blender-style, in the browser). It could already load URDFs, rig joints, replay LeRobot episodes, and inspect motion frame-by-frame. An open-source project developed by one of our teammates (Nikerane), started December 2025. The `main` branch (20 commits) was the pre-existing baseline. During the hackathon we built the `hkgenesis` branch on top of this environment.
- **urdf-ops** — Training-operations workspace. Split out of urdf-studio by amtellezfernandez before the hackathon. Already had a Vite + FastAPI stack, the keypoint-observation contract (`v1`) with validation endpoints, and `/training/*` endpoints scaffolded. Earliest commits from December 2025.
- **LeRobot** (Hugging Face) — Open-source robot framework (Apache 2.0). Used unmodified. Provides SO-101 motor drivers, calibration, teleop, dataset recording, and policy training (ACT).
- **i-love-urdf** — URDF parsing library (npm package). Used as a dependency by urdf-studio. Pre-existing.
- **SO-101 robot arms** — Physical hardware (two arms: leader + follower with gripper). Pre-purchased, assembled, and motor IDs configured before the hackathon.

## What was built during the hackathon

- **pulsar** — Interactive storyboard / vision pitch for the 8-stage REAL2SIM pipeline. Built from scratch by rayan-elidrissi. Pure frontend (HTML + React loaded from CDN), no backend. Walks a viewer through: capture → clean plate → backdrop → splat field → asset placement → rig/DOF → handoff.
- **simu_gen** — Image-to-3D-world generator. Built from scratch by marinabar. A VLM-driven pipeline that takes one photo, segments objects, builds a gaussian-splat background (via World Labs API), and generates textured 3D meshes (via Replicate API). Comes with a Three.js + Rapier physics viewer.
- **HK cargo world** (urdf-studio `hkgenesis` branch) — ~22 commits on top of urdf-studio main. Adds: a Hong Kong port cargo scene with grabbable containers, Genesis physics simulation for the SO-101, leader teleop synced to Genesis, SO-101 camera POV fixes, dataset export aligned with LeRobot v3 format, and browser state recovery.
- **replay_episode.py** — Glue script that takes a Studio-exported LeRobot v3 episode and plays it on the real SO-101 follower arm. Handles radians→degrees conversion and virtual joint filtering.
- **docs/** — All architecture and component documentation (6 docs + README).
- **episodes/** — One sample recorded episode (`so101_new_calib_ep01`) in LeRobot v3 parquet format (386 frames, 30 fps, 7 joints).
- **outputs/captured_images/** — Hand-eye camera captures from the real SO-101 gripper camera.
- **This repo's structure** — Git submodule wiring, `README.md`, `.gitmodules`, `.gitignore`.

## Pre-existing assets, libraries, and components brought in

| Asset | Source | License | Role |
|---|---|---|---|
| urdf-studio (`main` branch) | Nikerane's project | Proprietary (all rights reserved) | Core workbench |
| urdf-ops | amtellezfernandez/urdf-ops | AGPL-3.0 | Training-operations workspace |
| LeRobot v0.5.2 | huggingface/lerobot | Apache 2.0 | Robot drivers + training |
| i-love-urdf | npm package | — | URDF parsing |
| World Labs API | worldlabs.ai | Paid API | Gaussian splat generation (simu_gen) |
| Replicate API | replicate.com | Paid API | Inpainting + mesh generation (simu_gen) |
| Three.js + React | CDN / npm | MIT | 3D rendering across components |
| Rapier | npm | Apache 2.0 | Physics in simu_gen viewer |
| Genesis | genesis-embodied-ai | — | Physics sim in urdf-studio HK world |
| React + Babel (CDN) | unpkg.com | MIT | pulsar frontend |
| SO-101 arms + Feetech motors | Waveshare | Hardware | Physical robot layer |

## What is fully functional

- **pulsar** — The storyboard works end-to-end in a browser. All 8 stages render with ASCII art and canvas wireframes. No server, no API keys needed.
- **urdf-studio sample motion** — Load the sample URDF (`lekiwi`), play back episodes, inspect joints frame-by-frame with the graph overlay. Smoke-tested.
- **SO-101 teleop** — Leader arm drives follower arm in real time. Calibrated and verified.
- **SO-101 calibration** — Both arms calibrated. Calibration files saved and backed up.
- **replay_episode.py** — Plays a Studio-exported episode on the real SO-101 follower. Radians→degrees conversion and virtual joint filtering tested.
- **urdf-ops keypoint contract** — `POST /keypoint-observations/validate` endpoint works. Schema validation and coverage reporting functional.
- **simu_gen pipeline** — Individual stages run and produce assets. The viewer loads worlds and renders gaussian splats with physics.
- **Hand-eye camera** — SO-101 gripper camera captures images. Outputs saved in `outputs/captured_images/`.

## What is mocked, simulated, or unfinished

### Mocked / simulated
- **pulsar asset placement and rigging** — The wireframe crane with 5 sliders is a pre-scripted demo with hardcoded joint ranges. It does not load real URDFs or run inverse kinematics. It is a UI mock of what urdf-studio actually does.
- **simu_gen depends on paid external APIs** (World Labs, Replicate). There is no offline pipeline. Every world generation costs money and requires internet.

### Unfinished / not yet connected
- **Policy training** — Not completed during the hackathon. No policy has been trained on SO-101 data.
- **Cross-platform** — Everything was developed and tested on macOS (Apple Silicon) only. Linux and Windows paths are documented but untested.
- **`replay_episode.py` robustness** — Works for the sample episode. Not tested with varied datasets, longer episodes, or edge cases like mid-replay disconnection recovery.
