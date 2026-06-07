# pulsar

Pulsar is the project's vision demo. It is an interactive storyboard that walks
through the 8-stage REAL2SIM pipeline for ports: from one photo of a terminal to
a rigged, controllable digital twin you can hand to a robot workbench.

It is the pitch, not the engine. Pulsar shows what the pipeline does and why it
matters. The heavy compute (the real reconstruction) lives in `simu_gen`. Pulsar
is a guided walkthrough you click through, screen by screen.

- Source: https://github.com/rayan-elidrissi/pulsar
- Lives in: `pulsar/`
- Entry point: `pulsar/Real2Sim.html`

---

## What it is

A single-page web app. No build step, no server-side code. It is plain HTML plus
React and Babel loaded from a CDN, with the app split into `.jsx` files that the
browser compiles in place.

The frame is a wizard: a left rail lists the 8 pipeline stages, a center stage
shows the current step, and a footer steps you forward. A "Tweaks" panel lets you
change cosmetic things (accent color, ASCII glyph density, splat count, grid).

The look is a terminal/engineering aesthetic. Images are rendered as live ASCII.
3D assets are drawn as rotating wireframes on a canvas. The "gaussian splat" view
is a generated cloud of dots. None of this is real reconstruction — it is a
faithful-looking dramatization of each stage so a viewer understands the flow.

Where it sits in the loop:

```
real image -> [ PULSAR shows the pipeline ] -> rig in URDF Studio -> train -> replay on real arm
              real photo -> sim twin (the story Pulsar tells)
```

The last stage of Pulsar literally hands off to URDF Studio (it opens
`https://www.urdfstudio.com/`), which is the next component in the loop.

---

## The 8 stages it shows

The stages come from the `STEPS` list in `pulsar/r2s-data.jsx`. Each is one
screen in the wizard.

| # | Label | What the screen shows |
|---|---|---|
| 00 | Brief | The why. The failure library you want to rehearse, and a "Begin capture" button. |
| 01 | Capture | Ingest one image (or video) of the terminal. Drop a file or use the sample frame. Shows resolution, estimated field of view, a geo-anchor, and a parse-confidence readout. |
| 02 | Clean Plate | Strip out everything that moves or is transient — trucks, people, shadows, water glare, birds, lens noise. A slider wipes from raw capture to clean plate. Only the static terminal survives. |
| 03 | Backdrop | Reconstruct the static environment as layers: quay deck plane, harbour water plane, far skyline billboard, gantry rail splines. You can toggle each layer. |
| 04 | Splat Field | Lift the scene to 3D. Shows a gaussian-splat field (2.6M splats) and the mesh proxies extracted from it (crane, vessel, RTG, AGV). |
| 05 | Asset Place | Drop equipment meshes onto the reconstructed quay from a library. Each asset carries a degree-of-freedom count. You orbit the scene and add more. |
| 06 | Rig / DOF | Assign degrees of freedom to the placed crane. Five joints, each with a slider and an axis type (revolute / prismatic / fixed). The wireframe crane moves in real time as you drag. |
| 07 | Handoff | Package the rig and export it. Shows the export bundle (URDF, joints, collision, scene graph, splat field, scenario pack) and opens URDF Studio. |

> Note on numbering: the brief calls this an "8-stage" pipeline and there are 8
> screens (00 through 07). The progress label in the left rail counts stages
> `00 / 07`, i.e. the 8 screens indexed from zero.

---

## The port failure scenarios

The whole demo is built around one idea on the Brief screen: rehearse the worst
physical failure in simulation before it happens on the live apron. The failure
library is defined in `FAILURES` in `pulsar/r2s-data.jsx`:

| Code | Scenario | Severity |
|---|---|---|
| F-01 | Boom collision with vessel superstructure | critical |
| F-02 | AGV path conflict at apron intersection | high |
| F-03 | Spreader twist-lock mis-seat under wind | high |
| F-04 | Power loss mid-hoist — load swing arrest | critical |
| F-05 | Sensor dropout on gantry travel limit | moderate |

These are the reason the twin needs real degrees of freedom: a crane that can
luff, hoist, travel, and skew is a crane that can collide, mis-seat, or swing.

### The equipment it places

The asset library (`MESH_LIBRARY` in `pulsar/r2s-data.jsx`):

| Code | Asset | DOF | Type |
|---|---|---|---|
| STS-04 | Ship-to-Shore Crane | 5 | dynamic, critical |
| RTG-12 | RTG Yard Crane | 3 | dynamic |
| AGV-27 | Automated Guided Vehicle | 2 | dynamic, fleet |
| VSL-01 | Container Vessel | 1 | static |
| BOX-INF | Container Stack | 0 | static, instanced |

### The crane rig

The Rig / DOF screen rigs the Ship-to-Shore crane with 5 joints
(`CRANE_JOINTS` in `pulsar/r2s-data.jsx`):

| Joint | Axis | Range | Drive |
|---|---|---|---|
| Gantry Travel | prismatic | -14 to 14 m | rail bogies (crane moves along the quay rail) |
| Boom Luff | revolute | 0 to 78 deg | luffing winch (raises boom clear of the vessel) |
| Trolley Travel | prismatic | 0 to 100 % | trolley drive (carries the spreader along the boom) |
| Spreader Hoist | prismatic | 0 to 100 % | main hoist (vertical lift of spreader and load) |
| Spreader Skew | revolute | -30 to 30 deg | anti-snag servo (rotates load to align with cells) |

---

## How to open and run it

It is a static page, but you cannot just double-click the file. The HTML loads
its `.jsx` files over HTTP, so opening with `file://` will fail (browser
security blocks it). Run any local static server from the `pulsar/` folder and
open `Real2Sim.html`.

Using Python (already on most machines):

```bash
cd pulsar
python3 -m http.server 8080
# then open http://localhost:8080/Real2Sim.html
```

Or with Node:

```bash
cd pulsar
npx serve .
# open the printed URL, then add /Real2Sim.html
```

No install, no API keys, no GPU. Everything runs in the browser. React, ReactDOM,
and Babel are pulled from `unpkg.com`, so you need internet on first load.

How it is wired (from `pulsar/Real2Sim.html`): the page mounts into `#root` and
loads these scripts in order:

- `tweaks-panel.jsx` — the cosmetic tweaks panel
- `r2s-ascii.jsx` — the ASCII image renderer
- `r2s-viewers.jsx` — canvas wireframe viewers and the splat field
- `r2s-data.jsx` — the pipeline definition, asset library, crane joints, failures
- `r2s-atoms.jsx` — small shared UI pieces
- `r2s-steps1.jsx` — screens 00–03 (Brief, Capture, Clean, Backdrop)
- `r2s-steps2.jsx` — screens 04–07 (Splat, Place, Rig/DOF, Handoff)
- `r2s-app.jsx` — the wizard shell, navigation, and mount

> There is also a large prebuilt `pulsar/index.html` (a single self-contained
> bundle). `Real2Sim.html` is the readable, split-file version to run from this
> repo.

The only asset the live wizard reads is `assets/port-scene.jpg` (the sample
terminal image it renders as ASCII and as the splat field). The other files in
`assets/` and `uploads/` are source media used when building the standalone
bundle.

---

## Screenshots

In `pulsar/screenshots/`:

| File | Shows |
|---|---|
| `intro.png` | Stage 00 Brief. The "Rehearse the worst failure before it ever happens" headline, the F-01..F-05 failure library, and the source terminal rendered as ASCII. |
| `splat.png` | Stage 04 Splat Field. The gaussian-splat point cloud plus the four extracted mesh proxies (sts_quay, feeder_hull, rtg_yard, agv_unit) with triangle counts. |
| `place.png` | Stage 05 Asset Place. Wireframe equipment dropped onto the splat scene, with the equipment library on the right (Ship-to-Shore Crane and RTG marked PLACED). |
| `dof.png` | Stage 06 Rig / DOF, joint panel. The 5-joint tree for the crane with sliders and revolute/prismatic/fixed axis toggles; viewport still loading. |
| `dof2.png` | Stage 06 Rig / DOF, with the wireframe crane drawn. Same joint panel beside a live kinematic preview of the rigged Ship-to-Shore crane. |
