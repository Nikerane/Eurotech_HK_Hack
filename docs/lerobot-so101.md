# LeRobot SO-101 (real-robot layer)

This is the layer that controls the physical SO-101 robot arm. It uses
[LeRobot](https://github.com/huggingface/lerobot), Hugging Face's robot framework,
which is vendored here as a git submodule at `./lerobot/`.

This is the last step of the project loop:
**real image -> sim world -> rig in urdf-studio -> train -> replay on the real arm.**
Whatever you build in simulation ends up running here, on real motors.

## What this layer does

LeRobot gives you everything for the real arm:

- **Find ports** — figure out which USB port each arm is on.
- **Calibrate** — map raw motor encoder values to joint angles.
- **Teleop** — drive the follower arm by moving the leader arm by hand.
- **Record datasets** — save teleop sessions as LeRobot datasets.
- **Train** — train a policy (e.g. ACT) on those datasets.
- **Replay** — play a recorded or Studio-exported motion back on the arm.

On top of LeRobot, this repo adds one glue script: `replay_episode.py`. It takes
an episode that URDF Studio exported and plays it on the real follower arm.

## Hardware in this project

Two SO-101 arms. The **follower** has the gripper and is the one that actually
does the work. The **leader** is moved by hand to drive the follower during teleop.

| Arm | Port |
|---|---|
| Follower (with gripper) | `/dev/tty.usbmodem5AB01581111` |
| Leader (no gripper) | `/dev/tty.usbmodem5A460857481` |

Your ports will differ. Use `lerobot-find-port` to find them.

## Full bring-up

The complete setup is in [`docs/setup.md`](./setup.md). Read that first if the
arm has never been brought up on this machine. It covers, in order:

1. Install LeRobot (conda env, ffmpeg, `pip install -e ".[feetech]"`).
2. Find USB ports (`lerobot-find-port`).
3. Verify motor IDs (only for DIY kits).
4. Calibrate both arms (`lerobot-calibrate`).
5. Teleop smoke test (`lerobot.scripts.lerobot_teleoperate`).
6. Camera setup (`lerobot-find-cameras opencv`).

Calibration files live in `~/.cache/huggingface/lerobot/calibration/`. They are
what makes a trained policy transfer to this specific robot. Back them up.

This doc does not repeat that guide. It focuses on the replay script.

## Replaying a Studio episode: `replay_episode.py`

`replay_episode.py` plays back a LeRobot **v3** episode on the SO-101 follower.
The episode is what URDF Studio exports after you rig and animate a scene in sim.

### What it does

1. Reads the dataset's `meta/info.json` to get the joint names and FPS.
2. Loads every frame for the chosen episode from the parquet files under `data/`.
3. Connects to the follower arm over USB.
4. For each frame, converts the joint positions and sends them to the arm,
   sleeping to hold the dataset's frame rate.

### Usage

```bash
python replay_episode.py \
    --dataset /path/to/unzipped/so101_new_calib_v3 \
    --episode 0 \
    --port /dev/tty.usbmodem5AB01581111
```

Arguments:

| Flag | Default | Meaning |
|---|---|---|
| `--dataset` | (required) | Path to the **unzipped** dataset folder (the one with `meta/` and `data/` inside). |
| `--episode` | `0` | Which episode index to replay. |
| `--port` | `/dev/tty.usbmodem5AB01581111` | USB port of the follower arm. |
| `--fps` | dataset FPS | Override the playback frame rate. Default uses the FPS from `info.json` (30 in our episode). |

The dataset is a Studio export. Studio gives you a `.zip` — unzip it first, then
point `--dataset` at the unzipped folder.

When it runs, it prints the joint names, FPS, and frame count, then waits for you
to press **Enter** before moving the arm. Keep a hand near the power switch the
first time. It disconnects the arm cleanly even if you Ctrl+C.

### Two details that matter

**1. Radians -> degrees.** URDF Studio exports joint positions in radians,
because that is the URDF convention. The SO-101 follower expects degrees. So the
script converts every value with `math.degrees(val)` before sending it
(`replay_episode.py:108`). If you skip this conversion, the arm barely moves
(a full radian is only about 57 degrees), so this is the key step.

**2. Virtual joints.** The URDF has a joint named `gripper_frame_joint` that does
not map to any real motor. It is a frame in the model, not a servo. The script
keeps a set `VIRTUAL_JOINTS = {"gripper_frame_joint"}` (`replay_episode.py:81`)
and skips any joint in it, so only the six real motors get commands. It also
strips a `.pos` suffix from names, so it handles both old Studio exports
(`gripper`) and new ones (`gripper.pos`).

### Episode data shape

This is the layout `replay_episode.py` reads, from
`episodes/so101_new_calib_ep01/meta/info.json`:

- `codebase_version`: `v3.0` (LeRobot v3 dataset format).
- `robot_type`: `so101_new_calib`.
- `fps`: `30`.
- `total_episodes`: 1, `total_frames`: 386.
- `data_path`: `data/chunk-{chunk_index:03d}/file-{file_index:03d}.parquet` —
  frames are stored in parquet chunks, which is why the loader walks every
  `chunk-*/` dir and reads each `.parquet` file.
- `features.action` and `features.observation.state`: both `float32`, shape `[7]`,
  with these seven names in order:

  ```
  gripper_frame_joint, gripper, wrist_roll, wrist_flex,
  elbow_flex, shoulder_lift, shoulder_pan
  ```

Note the first name, `gripper_frame_joint`, is the virtual joint the script
drops. That leaves six real motors: `gripper`, `wrist_roll`, `wrist_flex`,
`elbow_flex`, `shoulder_lift`, `shoulder_pan`. Each frame's `action` is a
7-element list of radians, matched to these names by position.

## Where this fits

LeRobot is what makes the digital twin real. You rig and animate the scene in
URDF Studio, export the motion as a v3 episode, and `replay_episode.py` plays it
on the actual SO-101. The same arm and calibration also feed teleop and dataset
recording, so motion can flow both ways: from the real arm into training data,
and from sim/training back onto the real arm.
