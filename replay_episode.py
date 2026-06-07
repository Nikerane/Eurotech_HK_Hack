"""
Replay a Studio-exported LeRobot v3 zip on the SO-101 follower arm.

Usage:
    python replay_episode.py \
        --dataset /path/to/unzipped/so101_new_calib_v3 \
        --episode 0 \
        --port /dev/tty.usbmodem5AB01581111

The Studio exports joint positions in radians (URDF convention).
This script converts them to degrees before sending to the follower.
"""

import argparse
import json
import math
import time
from pathlib import Path

import pyarrow.parquet as pq


def load_frames(dataset_root: Path, episode_idx: int) -> list[dict]:
    """Read all frames for one episode from the parquet chunks."""
    data_dir = dataset_root / "data"
    frames = []
    for chunk_dir in sorted(data_dir.iterdir()):
        if not chunk_dir.is_dir():
            continue
        for pq_file in sorted(chunk_dir.glob("*.parquet")):
            table = pq.read_table(pq_file)
            for row_idx in range(table.num_rows):
                row = {col: table.column(col)[row_idx].as_py() for col in table.column_names}
                if row.get("episode_index") == episode_idx:
                    frames.append(row)
    frames.sort(key=lambda r: r.get("frame_index", 0))
    return frames


def extract_joint_names(info: dict) -> list[str]:
    """Extract joint names from dataset info.json.

    URDF Studio exports names as ``{"motors": ["shoulder_pan.pos", ...]}``.
    """
    names = info["features"]["action"]["names"]
    if isinstance(names, dict):
        # {"motors": [...]} or {"joints": [...]}
        return names.get("motors") or names.get("joints") or list(names.values())[0]
    return names


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, help="Path to unzipped dataset folder")
    parser.add_argument("--episode", type=int, default=0)
    parser.add_argument("--port", default="/dev/tty.usbmodem5AB01581111")
    parser.add_argument("--fps", type=float, default=None, help="Override FPS (default: use dataset FPS)")
    args = parser.parse_args()

    dataset_root = Path(args.dataset)

    info = json.loads((dataset_root / "meta" / "info.json").read_text())
    joint_names = extract_joint_names(info)
    fps = args.fps or info.get("fps", 30)
    print(f"Joint names: {joint_names}")
    print(f"FPS: {fps}, Episode: {args.episode}")

    frames = load_frames(dataset_root, args.episode)
    if not frames:
        print(f"No frames found for episode {args.episode}")
        return
    print(f"Loaded {len(frames)} frames")

    # Connect to follower
    from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig
    config = SO101FollowerConfig(port=args.port, id="follower_arm")
    robot = SO101Follower(config)
    robot.connect()

    # Virtual URDF joints that don't map to real motors on the follower
    VIRTUAL_JOINTS = {"gripper_frame_joint"}

    # Build a mapping from dataset joint name → motor name (without .pos suffix)
    # Handles both "gripper" (old Studio export) and "gripper.pos" (new export)
    joint_to_motor: dict[str, str] = {}
    for name in joint_names:
        if name.endswith(".pos"):
            motor = name.removesuffix(".pos")
        else:
            motor = name
        if motor in VIRTUAL_JOINTS:
            continue
        joint_to_motor[name] = motor

    print(f"Motors: {list(joint_to_motor.values())}")

    try:
        input(f"Press Enter to start replaying episode {args.episode} ({len(frames)} frames)...")
        for frame in frames:
            t0 = time.perf_counter()

            # Studio exports radians → convert to degrees for the follower
            action_rad = frame["action"]
            action = {}
            for name, val in zip(joint_names, action_rad):
                motor = joint_to_motor.get(name)
                if motor is not None:
                    action[f"{motor}.pos"] = math.degrees(val)

            robot.send_action(action)

            dt = time.perf_counter() - t0
            time.sleep(max(1.0 / fps - dt, 0.0))

        print("Replay complete.")
    finally:
        robot.disconnect()


if __name__ == "__main__":
    main()
