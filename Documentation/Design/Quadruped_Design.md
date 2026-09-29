# ChromaSniff — Quadruped Integration Design

## 1. Purpose

The quadruped integration carries the existing ChromaSniff V1.1 handheld barrel as a detachable inspection payload. The robot integration is designed as a payload adapter rather than a redesign of the handheld sensing barrel.

## 2. Robot concept

The current CAD uses a **Go2-class placeholder** for the robot body. Trunk dimensions, hip offsets, leg lengths and bolt pattern are explicitly marked for verification against manufacturer URDF/STEP before fabrication.

The model contains:

- trunk
- head
- chin LiDAR envelope
- four 2-link legs using an IK pose
- fixed payload plate
- adapter base plate
- hinge cheeks
- tilting cradle
- Arca-type clamp
- clamp/tilt-lock hardware
- adapter electronics box
- e-stop button
- cable/service loop
- validation markers

## 3. Payload mount

```text
QUADRUPED TRUNK
      │
      ▼
Robot payload plate
      │
      ▼
Adapter base plate
      │
      ▼
Hinge / tilting mechanism
      │
      ▼
Cradle plate + Arca clamp
      │
      ▼
38 mm dovetail on ChromaSniff
      │
      ▼
CHROMASNIFF HANDHELD BARREL
```

The payload tilt is represented as nozzle-down rotation about a hinge axis aligned with robot Y. The model currently uses 0–20° as the validated design range, with 0°, 10° and 20° explicitly evaluated.

## 4. Robot configuration

Robot mode removes the handheld grip and uses the robot adapter on the same dovetail. The rear connector supplies robot power, e-stop and data. The CAD integration models a 33.6 V maximum robot bus and a required 24 V DC-DC stage in the adapter.

Robot operation is defined as:

- continuous Tier-1 cueing
- vapour-mode testing
- chemical card loaded by hand before deployment
- no swab mode on the robot

## 5. Current placeholder parameters

| Parameter | Current model value | Status |
|---|---:|---|
| Robot mass | 15 kg | placeholder/published-class reference |
| Rated payload | 7 kg | use lowest stated figure; verify robot model |
| Payload derate | 0.5 | design assumption |
| Standing hip height | 290 mm | placeholder |
| Crouched hip height | 160 mm | placeholder |
| Top plate Z | 340 mm | placeholder |
| Mount hinge X | 160 mm | placeholder |
| Mount hinge Z | 395 mm | placeholder |
| Payload tilt | 10° nominal | modelled detents 0/10/20° |
| Maximum tilt | 20° | current integration limit |
| Maximum total height | 600 mm | project constraint/placeholder |

These values are not fabrication-approved dimensions.

## 6. Validation performed by the integration macro

The integration macro checks the standing and crouched robot poses over the configured tilt angles. It evaluates:

1. payload-to-robot clearance
2. hot-zone clearance from head/LiDAR
3. card-door accessibility
4. hinge side gap
5. total robot + payload height
6. nozzle reach ahead of robot front
7. LiDAR hemisphere occlusion
8. combined centre-of-gravity shift
9. payload mass against derated payload limit
10. cable/service-loop length
11. robot input-voltage mismatch and DC-DC requirement

The model also explicitly notes that robot roll-over/flip-recovery behaviours should be disabled while this payload is mounted.

## 7. Critical engineering verification before fabrication

- Replace Go2-class placeholders with the exact robot's URDF/STEP geometry.
- Verify the robot top-plate bolt pattern.
- Weigh the actual handheld and mount.
- Measure the actual centre of gravity.
- Verify clamp retention under gait vibration.
- Verify hot-zone clearance from head/LiDAR.
- Verify LiDAR occlusion with the real sensor.
- Verify e-stop cuts heater enable in hardware.
- Verify cable slack across the full tilt range.
- Verify robot power voltage and connector current ratings.

## 8. Design principle

The robot is a carrier and motion platform. The ChromaSniff barrel remains the primary chemical-analysis payload, while the quadruped adapter provides mechanical attachment, power/data integration and safe positioning.
