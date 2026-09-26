# NITK ME318 — Centrifugal Pump (Fusion 360)

A Fusion 360 Python script that generates a complete centrifugal pump 3D model per the NITK ME318 specification.

## What It Creates

| Component | Details |
|-----------|---------|
| **Back Plate** | 46 mm OD × 2 mm solid disc |
| **Hub** | 10 mm OD × 14 mm central cylinder |
| **Vanes** | 6 backward-curved, 2 mm thick, 12 mm tall |
| **Volute** | Archimedean spiral (R 29→32 mm), lofted cross-sections (∅ 3→10 mm) |
| **Outlet** | 20 mm vertical extension with ∅ 10 mm exit |
| **Export** | STEP file → `~/Desktop/NITK_Centrifugal_Pump.step` |

## Volute Spiral Markers

| Marker | Angle | Radius | Profile ∅ |
|--------|-------|--------|-----------|
| 29 | 0° | 29 mm | 3.0 mm |
| 30 | 90° | 30 mm | 4.0 mm |
| 31 | 180° | 31 mm | 5.5 mm |
| 32 | 270° | 32 mm | 7.0 mm |

## How to Run in Fusion 360 (Mac)

1. **Open Fusion 360** on your Mac.

2. **Create a New Design** — `File` → `New Design`.

3. **Open Scripts Manager** — `Tools` → `Add-Ins` → click the **Scripts** tab.

4. **Create a New Script** — click the green **+** button:
   - Name: `pump_model`
   - Language: **Python**

5. **Paste the Code** — open `pump_model.py` from this repo, copy **everything**, and paste it into the Fusion 360 script editor (replacing any default code).

6. **Save** the script.

7. **Run** — click the ▶ (play) button. Wait a few seconds.

8. **Done!** You'll see:
   - The impeller with 6 curved vanes in the design browser
   - The volute spiral casing as a separate body
   - A STEP file on your Desktop

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "No active design" error | Make sure you did `File → New Design` first |
| Vane profile error | Ensure you're on a fresh, empty design |
| STEP export fails | Check Desktop write permissions; export manually via `File → Export` |
| Model looks too big/small | All units are already converted to cm internally — don't change values |

## For CFD (ANSYS Fluent)

1. Open the exported `.step` file in ANSYS SpaceClaim/DesignModeler
2. Use **Boolean Subtract** to remove impeller volume from casing volume
3. Set **Inlet** = 18 mm face (velocity inlet), **Outlet** = 10 mm face (pressure outlet)
4. Apply rotating mesh / frozen rotor for the impeller region

## Files

- `pump_model.py` — Fusion 360 Python script (the only file you need)
- `README.md` — This file
