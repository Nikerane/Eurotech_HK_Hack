# simu_gen

Turn one photo into an interactive 3D sim you can walk around in.

simu_gen takes a single image. It builds a world from it: a gaussian-splat background at real-world (metric) scale, plus separate 3D object meshes with estimated size and mass. You can load that world in a browser viewer and move objects with physics.

This is the first stage of the REAL2SIM loop. Real image -> simu_gen world -> rig in urdf-studio -> train -> replay on the real arm.

Origin repo: https://github.com/marinabar/simu_gen

## What it does

Given one input image, simu_gen:

1. Looks at the image and lists the movable objects in it.
2. Estimates each object's real size (meters) and mass (kg).
3. Removes the objects from the image to get a clean empty background ("plate").
4. Builds a navigable 3D environment from that clean plate.
5. Builds a textured 3D mesh for each object.

The result is a self-contained `worlds/<slug>/` folder. The viewer loads it, scales each mesh to its true size, and gives it physics mass.

It uses:
- A vision-language model (VLM) to read the image and list objects.
- Replicate for image edits and meshes: `google/nano-banana-2` (inpaint / object removal) and `tencent/hunyuan-3d-3.1` (mesh from image). Meshy is an optional alternate mesh provider.
- World Labs to build the gaussian-splat background world.

## Pipeline stages

The pipeline runs as four stages. Each stage is a VLM prompt file in `orchestrator/` plus a backing script in `scripts/`. Each stage writes files to disk so you can stop, inspect, and resume.

```
input image
  ├── image analysis + object list        (VLM, orchestrator/uncover.md)
  ├── clean plate: remove objects          (Replicate nano-banana, orchestrator/plate.md)
  ├── 3D environment from clean plate       (World Labs, orchestrator/world.md)
  └── one mesh per object                  (Replicate hunyuan3d, orchestrator/3d.md)
          ↓
  interactive scene (Spark splats / Three.js / Rapier physics)
```

| Stage | Prompt file | What it produces |
|-------|-------------|------------------|
| Image analysis | `orchestrator/uncover.md` | Scene description, object candidates, size/mass estimates. Writes `image.json` and one `object.json` per object. |
| Clean plate | `orchestrator/plate.md` | A new source image with the objects removed (the empty "plate"). |
| World | `orchestrator/world.md` | The gaussian-splat background, collision mesh, panorama, thumbnail. |
| Per-object mesh | `orchestrator/3d.md` | One textured `.glb` mesh per confirmed object. |

`orchestrator/rules.md` describes the order and the file conventions. `orchestrator/image-analysis-contract.md` holds the exact JSON schema the analysis stage must follow.

### Stage notes

- **Image analysis** extracts only single, cleanly liftable items. It skips floors, walls, rugs, and fixed parts of the scene. It never groups items (no "table with chairs"). It estimates each object's height in meters (used to scale the mesh) and mass in kg (used for physics).
- **Clean plate** is removal-only. It names what to remove in one edit pass and gets back a background with the objects gone. The plate is saved as a new indexed source file (e.g. `1-room-plate.png`), not overwriting the original `0-room.png`.
- **World** feeds the clean plate plus a text caption (the original scene description with removed objects subtracted) to World Labs. The caption describes the empty environment, not the objects.
- **Per-object mesh** isolates one object onto a clean white background (image edit), then turns that into a textured mesh. Hunyuan is the default 3D provider (`--face-count 50000`, `--enable-pbr true`, `--generate-type Normal`).

## Requirements and API keys

- Node.js 18+
- World Labs API key (`WORLD_LABS_API_KEY`) — builds the gaussian-splat world.
- Replicate API key (`REPLICATE_API_KEY`) — image edits and object meshes.

Get keys at https://worldlabs.ai and https://replicate.com.

## Install and run

```bash
cd simu_gen
npm install
npm run setup    # interactive prompt, writes keys to .env
npm run dev      # viewer at http://localhost:5173
```

`npm run setup` asks for the two API keys and saves them to `.env`. You can also copy `.env.example` to `.env` and fill it in by hand.

Other scripts: `npm run build` and `npm run preview` (both run against the `app` workspace).

## Running the pipeline

Put your input image in `input/`. Then drive the four orchestrator prompts in order with a VLM.

### Full pipeline (one shot)

Follow `orchestrator/rules.md`. It runs all four stages end to end: inspect state, analyze the image, confirm objects, make the plate, generate the world, then generate one mesh per object. Generated assets land in `worlds/<slug>/output/`, and the running viewer updates from disk in real time.

### Individual stages (run scripts directly)

You can call the backing scripts yourself. Each one blocks until done.

```bash
# stage and inspect project state
node scripts/project/project-state.mjs --world "<slug>" --stage-input

# generate the World Labs world from the newest source image
node scripts/world/generate-world.mjs --world "<slug>" --prompt "<empty-scene caption>"

# generate one object mesh
node scripts/asset-pipeline/generate-single-asset.mjs --world "<slug>" --object-id "<id>" --image-edit-prompt "<extraction prompt>"

# run a single image edit (e.g. a clean plate)
node scripts/image-edit/generate-edit.mjs --image "<path>" --prompt "<prompt>" --output-dir "<dir>" --output-slug "<slug>"

# re-download any provider assets that are missing locally
node scripts/project/ensure-local-assets.mjs --from "<world-or-request-json>"
```

Useful flags:
- `generate-world.mjs`: `--image <path>` to override the source, `--regenerate` to force a new world.
- `generate-single-asset.mjs`: `--regenerate` (new mesh from same reference), `--regenerate-reference` (new extraction + mesh), `--provider meshy|hunyuan`, `--face-count`, `--enable-pbr`, `--generate-type`.

## Output layout

Each world is one folder under `worlds/<slug>/`. Files are disk-first: any provider URLs stored in JSON are only for provenance and resume; the viewer always loads local files.

```
worlds/<slug>/
  project.json            project metadata
  image.json              merged scene + object analysis
  scene.json              editor placement state
  source/
    0-<slug>.<ext>        original input image
    1-<slug>-plate.png    clean plate (objects removed)
    <image>.json          per-image VLM analysis
  output/
    world/                gaussian splat (.spz), collision mesh (.glb), panorama, thumbnail
    <object>/
      object.json         identity + size/mass estimates
      <n>-<object>.glb    textured mesh
input/                    drop input images here
```

Generated files use an indexed naming scheme: `N-slug.ext`, where `N` is the generation index and `0` is the original. A hidden `.N-slug-request.json` sits beside each generated file with the request metadata. Use `ls -a <dir>` to see them.

## Viewer

The viewer is a Vite + React + Three.js app (`app/`). It renders gaussian splats with Spark and runs Rapier rigid-body physics. Object meshes are scaled to their estimated real-world size and given physics mass from the estimated kg.

Navigate in first-person or fly mode.

On-screen controls:

```
top-left     world list / object list / navigation mode / quality / depth-of-field
bottom-left  world render mode (Scene + Objects / Scene only / Objects only)
             object shading (Lit / Shaded Wireframe / Wireframe)
```

Keyboard shortcuts for the bottom-left modes:
- `Shift` + `1/2/3` — world render mode (Combined / Splat only / Objects only)
- `Alt` + `1/2/3` — object shading (Lit / Shaded Wireframe / Wireframe)
- `Alt` + `Shift` + `1/2` — viewer quality (Low / High)

Open a specific world at `http://localhost:5173/<slug>`.

## Object representation

Each object carries durable identity and physical estimates in `object.json`:

```json
{
  "object": {
    "id": "<slug>",
    "name": "<name>",
    "description": "<literal description>",
    "estimated_size_m": { "height": 0.0, "width": 0.0, "length": 0.0 },
    "estimated_mass_kg": 0.0,
    "source_images": [],
    "evidence": []
  }
}
```

`height` (meters) scales the mesh to true proportions in the world. `estimated_mass_kg` sets the rigid-body mass. `object.json` holds intent and provenance only — generated state (jobs, file lists, status) lives in the indexed artifacts and hidden request JSON beside it.
