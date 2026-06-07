# HONESTY.md

Eurotech x HKTE Hackathon — June 5–7, 2026

## What existed before the hackathon

- **urdf-studio** — A local robotics workbench (Blender-style, in the browser). It could already load URDFs, rig joints, replay LeRobot episodes, and inspect motion frame-by-frame. Nikerane's project, started December 2025. The `main` branch (20 commits) was the pre-existing baseline.
- **LeRobot** (Hugging Face) — Open-source robot framework (Apache 2.0). Used unmodified. Provides SO-101 motor drivers, calibration, teleop, dataset recording, and policy training (ACT).
- **i-love-urdf** — URDF parsing library (npm package). Used as a dependency by urdf-studio. Pre-existing.
- **SO-101 robot arms** — Physical hardware (two arms: leader + follower with gripper). Pre-purchased, assembled, and motor IDs configured before the hackathon.

## What was built during the hackathon

- **pulsar** — Interactive storyboard / vision pitch for the 8-stage REAL2SIM pipeline. Built from scratch by rayan-elidrissi. Pure frontend (HTML + React loaded from CDN), no backend. Walks a viewer through: capture → clean plate → backdrop → splat field → asset placement → rig/DOF → handoff.
- **simu_gen** — Image-to-3D-world generator. Built from scratch by marinabar. A VLM-driven pipeline that takes one photo, segments objects, builds a gaussian-splat background (via World Labs API), and generates textured 3D meshes (via Replicate API). Comes with a Three.js + Rapier physics viewer.
- **urdf-ops** — Training-operations workspace. Split out of urdf-studio by amtellezfernandez. Defines a keypoint-observation contract (`v1`) with validation endpoints. Scaffolds `/training/*` endpoints for policy training jobs. Has its own Vite + FastAPI stack.
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
- **pulsar is entirely a dramatization.** The ASCII renders, canvas wireframes, and splat-point clouds are artistic representations — not real 3D reconstruction. It is a vision pitch that looks faithful, but no actual compute happens. It is designed to tell the story, not to process data.
- **pulsar asset placement and rigging** — The wireframe crane with 5 sliders is a pre-scripted demo with hardcoded joint ranges. It does not load real URDFs or run inverse kinematics. It is a UI mock of what urdf-studio actually does.
- **simu_gen depends on paid external APIs** (World Labs, Replicate). There is no offline pipeline. Every world generation costs money and requires internet.

### Unfinished / not yet connected
- **Policy training** — Not completed. The setup guide's "Next Steps" section lists "Record a dataset" and "Train a policy (ACT)" as unchecked. No policy has been trained on SO-101 data during the hackathon.
- **The full REAL2SIM loop** — Each component works standalone, but the end-to-end chain (real image → simu_gen world → rig in urdf-studio → train → replay on SO-101 → hand-eye capture → feed back to simu_gen) has not been run through. The connections are defined and documented, not tested end-to-end.
- **simu_gen → urdf-studio handoff** — The data format and flow are specified, but loading simu_gen world assets (gaussian splats + object meshes) into urdf-studio's scene has not been wired.
- **Genesis physics** — Container grasping and real-time physics sync with teleop was being hardened during the final hours. The floor contacts commit ("Harden Genesis floor contacts") is the last commit on hkgenesis.
- **urdf-ops training endpoints** — The `/training/*` routes are scaffolded but do not run actual training jobs. The keypoint contract validates data shape; no real training pipeline consumes it yet.
- **SO-101 dataset recording** — No teleop dataset was recorded during the hackathon. The sample episode in `episodes/` was exported from Studio, not recorded from real teleop.
- **Camera→simu_gen loop closure** — The hand-eye camera captures images, but feeding one back into simu_gen to start a new world generation cycle is untested.
- **Multi-episode workflow** — Only one sample episode exists. Replay, retake, and dataset management in Studio work for that single episode but have not been exercised at scale.
- **Cross-platform** — Everything was developed and tested on macOS (Apple Silicon) only. Linux and Windows paths are documented but untested.
- **`replay_episode.py` robustness** — Works for the sample episode. Not tested with varied datasets, longer episodes, or edge cases like mid-replay disconnection recovery.
