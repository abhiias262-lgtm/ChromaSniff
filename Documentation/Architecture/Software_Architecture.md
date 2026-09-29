# ChromaSniff — Software & CAD Automation Architecture

## 1. CAD automation

The handheld FreeCAD macro builds `ChromaSniff_V1_1` and provides:

- `CS_MasterParameters`
- `CS_DesignNotes`
- `CS_ValidationReport`
- parameter-bound envelope objects
- configuration switching between handheld and robot modes
- gas-route redraw/checking

The robot integration macro builds `ChromaSniff_Robot_V1` and provides:

- `CS_RobotParameters`
- quadruped placeholder geometry
- fixed and tilting payload mounts
- handheld payload placement
- cable/service-loop geometry
- `CS_RobotValidation`
- CoG and nozzle-tip markers

## 2. Configuration model

The handheld CAD uses `Config_Robot`:

```text
0 → HANDHELD
1 → ROBOT
```

The robot integration also evaluates multiple robot poses and payload tilts rather than validating only one static configuration.

## 3. Coordinate frames

### Handheld frame P

```text
X = right
Y = forward toward nozzle
Z = up
```

### Robot frame R

The robot integration uses ROS REP-103 convention:

```text
X = forward
Y = left
Z = up
```

The payload is mounted nozzle-forward using a Z rotation followed by nozzle-down tilt around the robot Y hinge axis.

## 4. Validation software

The handheld validation checks:

- envelope containment
- allowed protrusions
- collisions
- parent/child containment
- thermal keep-out
- electronics clearance
- card-to-bulkhead gap
- camera/card optical alignment
- lens HFOV requirement
- optical path clearance
- service-access volumes
- exhaust separation
- gas-route completeness

The CAD brief records the V1.1 dry-run result as 49/49 passes for handheld and 43/43 for robot, with a negative test correctly flagging intentionally bad Pi/camera placement.

## 5. Robot validation

The robot integration evaluates standing and crouched poses across tilt positions including 0°, 10°, 20° and configured maximum tilt. It checks:

- payload/robot clearance
- hot-zone clearance from head/LiDAR
- card access
- hinge gap
- overall height
- nozzle reach
- LiDAR occlusion
- combined CoG shift
- payload limit
- cable routing/service slack
- robot power conversion requirement

## 6. Engineering status

The validation scripts are layout/geometry checks, not substitutes for thermal, structural, electrical or gait testing. Real STEP geometry and measured prototype masses must replace placeholders before fabrication.
