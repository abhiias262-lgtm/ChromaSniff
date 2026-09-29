# ChromaSniff — System Architecture

**Version:** V1.1  
**Source of truth:** `ChromaSniff_CAD_Handheld.py`, `ChromaSniff_Robot_Integration_v1.py`, and `ChromaSniff_CAD_Master_Design_Brief_claude(1).md`.

## 1. System overview

ChromaSniff is a pistol-grip handheld chemical screening platform whose same sensing barrel can be mounted as a detachable payload on a quadruped robot. The handheld CAD is parameterized for both configurations; robot integration adds a dedicated fixed/tilting payload mount, power/data interface, cable routing and validation.

The handheld operates with two sensing paths:

- **Tier-1:** continuous ambient-air cueing through a dedicated top-vented sensor cell.
- **Tier-2:** controlled vapour/card analysis through heating, cooling, optical card readout and downstream sensing.

Robot mode keeps Tier-1 cueing and vapour-mode testing, with a card loaded by hand before deployment. Swab mode is handheld-only.

## 2. Major subsystems

```text
CHROMASNIFF
├── Handheld / payload barrel
│   ├── Heated nozzle
│   ├── Vapour collection + Tenax trap
│   ├── Swab chamber
│   ├── Cooling path
│   ├── Chemical card + optical cell
│   ├── Tier-1 air cell
│   ├── Tier-2 downstream manifold
│   ├── Pumps + valves + scrubber
│   ├── SWV/SPE channel
│   ├── Raspberry Pi 5
│   ├── ESP32-S3 control PCB
│   └── Power + display + communications
│
└── Quadruped integration
    ├── Robot payload plate
    ├── Adapter base
    ├── Tilting cradle
    ├── 38 mm Arca-type clamp
    ├── Adapter DC-DC + fuse + e-stop
    ├── Rear power/data cable
    └── Mechanical/CoG/LiDAR/clearance validation
```

## 3. Mechanical interface

A single 38 mm Arca-type dovetail is the common mechanical payload interface. In handheld mode it carries the detachable grip; in robot mode it is clamped by the robot adapter. The rear connector provides robot power, e-stop loop and data.

## 4. Thermal zoning

The barrel is divided into HOT, WARM, INTERMEDIATE and COOL regions. The hot zone contains the Tenax trap/desorber, heated V2 and swab chamber. A thermal bulkhead separates this region from the cooling and analysis hardware. The card is downstream of the cooling length and has a 40 °C surface limit.

## 5. Control architecture

The CAD source models the physical placement of the compute/control hardware. Raspberry Pi 5 is assigned to camera, AI, UI, crypto and BLE. The ESP32-S3 main control PCB handles real-time control functions including heater/valve driving and safety-related logic.

## 6. Design status

All CAD dimensions remain placeholder envelopes until real manufacturer STEP/datasheet geometry is selected. The CAD brief explicitly requires replacing envelopes before freezing fabrication geometry.
