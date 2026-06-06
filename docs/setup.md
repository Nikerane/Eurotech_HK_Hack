# SO-101 LeRobot Setup Guide

Step-by-step record of bringing up the SO-101 robot arm with LeRobot on macOS (Apple Silicon).

## System Info

- **OS:** macOS 15 (Darwin)
- **Arch:** ARM64 (Apple Silicon)
- **Python:** 3.12 (conda environment)
- **LeRobot:** 0.5.2 (installed from source, editable)

---

## 1. Install LeRobot

### Prerequisites

- Conda (miniconda or miniforge)
- Git

### Create environment

```bash
conda create -y -n lerobot python=3.12
conda activate lerobot
```

### Solver fix (miniconda users)

If you see `conda-libmamba-solver` errors:

```bash
conda config --set solver classic
```

### Install ffmpeg

```bash
conda install ffmpeg=7.1.1 -c conda-forge
```

### Clone and install LeRobot

```bash
git clone https://github.com/huggingface/lerobot.git
cd lerobot
pip install -e ".[feetech]"
pip install 'lerobot[viz]'  # Rerun SDK for live camera display
```

### Verify

```bash
python -c "import lerobot; print('LeRobot', lerobot.__version__)"
# Output: LeRobot 0.5.2
```

---

## 2. Discover USB Ports

Connect one arm at a time via USB (both USB cable and power supply must be connected).

```bash
lerobot-find-port
```

The script prompts you to disconnect the arm, then identifies its port.

### Our ports

| Arm | Port |
|---|---|
| Follower (with gripper) | `/dev/tty.usbmodem5AB01581111` |
| Leader (no gripper) | `/dev/tty.usbmodem5A460857481` |

### Troubleshooting

If `ls /dev/tty.usb*` returns nothing:
- Make sure the **power supply** is connected (controller board lights up green LEDs)
- Use a **data-capable** USB cable, not charge-only
- On Waveshare boards, verify jumpers are on **B channel** (USB)

**macOS note:** No `sudo chmod 666` needed — macOS grants user access to `/dev/tty.usbmodem*` automatically. That step is only required on Linux.

---

## 3. Verify Motor IDs

If your kit is pre-assembled, motor IDs should already be configured. Calibration will fail if they're not.

Our kit came pre-configured. The calibration output confirmed all 6 joints were detected:

```
shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper
```

If motor IDs need to be set (DIY kit), run:

```bash
# Follower
lerobot-setup-motors \
    --robot.type=so101_follower \
    --robot.port=/dev/tty.usbmodem5AB01581111

# Leader
lerobot-setup-motors \
    --teleop.type=so101_leader \
    --teleop.port=/dev/tty.usbmodem5A460857481
```

This writes IDs to motor EEPROM. Only one motor connected at a time. Only needed once.

---

## 4. Calibrate Both Arms

Calibration maps raw encoder values to joint angles. Critical for policy transfer.

### Follower

```bash
lerobot-calibrate \
    --robot.type=so101_follower \
    --robot.port=/dev/tty.usbmodem5AB01581111 \
    --robot.id=follower_arm
```

### Leader

```bash
lerobot-calibrate \
    --teleop.type=so101_leader \
    --teleop.port=/dev/tty.usbmodem5A460857481 \
    --teleop.id=leader_arm
```

### Procedure for each

1. Move all joints to middle of range, press **Enter**
2. Move all joints (except wrist_roll) through their full range of motion
3. Press **Enter** to stop recording
4. Hold the zero pose and press **Enter**
5. Calibration file is saved to `~/.cache/huggingface/lerobot/calibration/`

### Calibration results (2026-06-06)

| Joint | Follower MIN | Follower MAX | Leader MIN | Leader MAX |
|---|---|---|---|---|
| shoulder_pan | 711 | 3422 | 766 | 3220 |
| shoulder_lift | 870 | 3266 | 920 | 3366 |
| elbow_flex | 845 | 3048 | 757 | 2932 |
| wrist_flex | 895 | 3206 | 896 | 3213 |
| gripper | 2047 | 3503 | 1873 | 3105 |

### Troubleshooting

If `JointOutOfRangeError`:
```bash
rm -rf ~/.cache/huggingface/lerobot/calibration/so101/
```
Then recalibrate.

---

## 5. Teleoperation (Smoke Test)

### Without camera

```bash
python -m lerobot.scripts.lerobot_teleoperate \
    --robot.type=so101_follower \
    --robot.port=/dev/tty.usbmodem5AB01581111 \
    --robot.id=follower_arm \
    --teleop.type=so101_leader \
    --teleop.port=/dev/tty.usbmodem5A460857481 \
    --teleop.id=leader_arm
```

- Press **Enter** to begin
- Move the leader arm by hand — the follower mirrors in real time
- **Ctrl+C** to stop

**Sanity check:** home pose → small motion → stop. If anything feels crunchy, resists, or goes the wrong direction → recalibrate.

---

## 6. Camera Setup

### Detect cameras

```bash
lerobot-find-cameras opencv
```

### macOS camera permissions

If you get `OpenCV: not authorized to capture video`, grant camera access:
- **System Settings → Privacy & Security → Camera** → enable Terminal
- Or run `python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"` to trigger the system prompt

### Our cameras

| Camera | Index | Resolution | Use |
|---|---|---|---|
| Follower onboard | 0 | 640×480 @ 30fps | Handeye (gripper-mounted) |
| MacBook built-in | 1 | 1920×1080 @ 30fps | Not used |

### Teleoperation with camera

```bash
python -m lerobot.scripts.lerobot_teleoperate \
    --robot.type=so101_follower \
    --robot.port=/dev/tty.usbmodem5AB01581111 \
    --robot.id=follower_arm \
    --robot.cameras='{handeye: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}}' \
    --teleop.type=so101_leader \
    --teleop.port=/dev/tty.usbmodem5A460857481 \
    --teleop.id=leader_arm \
    --display_data=true
```

The `handeye` camera is mounted on the follower's gripper. `--display_data=true` opens a Rerun window showing the live camera feed alongside joint positions.

---

## 7. Next Steps

- [x] Set up cameras
- [x] Teleoperate with cameras
- [ ] Record a dataset (`python -m lerobot.scripts.lerobot_record`)
- [ ] Train a policy (ACT)
- [ ] Deploy the trained policy

---

## Calibration Files

```
~/.cache/huggingface/lerobot/calibration/robots/so_follower/follower_arm.json
~/.cache/huggingface/lerobot/calibration/teleoperators/so_leader/leader_arm.json
```

Back these up — they're what makes a policy trained on this robot transferable.
