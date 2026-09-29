# ChromaSniff — Electronics Architecture

## 1. Compute and control

### Raspberry Pi 5

The CAD brief assigns the Raspberry Pi 5 to:

- camera processing
- AI/inference
- user interface
- cryptographic functions
- BLE

A Compute Module 5 on a custom carrier is identified as a V2 option to reduce volume.

### ESP32-S3 control PCB

The main control PCB is planned around an ESP32-S3-WROOM-1-N8R8 and includes the control/safety interface for:

- ADS1115 ADCs
- heater drivers
- valve MOSFET drivers
- MCP23017 I/O expansion
- INA226 power/current monitoring
- ATECC608B secure element
- heater watchdog
- independent over-temperature comparator/latch

## 2. Sensor electronics

### Tier-1 sensor cell

The dedicated top-vented cell contains:

- BME688 #1
- SGP41
- TGS2600
- TGS2602
- SHT45 #1
- dedicated fan

A custom sensor PCB is preferred over multiple breakout boards for compactness and response consistency.

### Tier-2 manifold

The downstream manifold contains:

- BME688 #2
- TGS2620
- SHT45 #2
- custom manifold sensor PCB

The manifold is downstream of the chemical card.

### Electrochemical channel

The SWV channel contains a compact potentiostat module and an edge-connected screen-printed electrode. This is a paired wet-swab channel and is handheld-only in the V1 architecture.

## 3. Power architecture

```text
HANDHELD BATTERY ─┐
                  ├─> IDEAL-DIODE OR ─> POWER BOARD
ROBOT INPUT ──────┘                         │
                                           ├─> 12 V heater/pump rail
                                           ├─> 5 V / 5 A Pi rail
                                           └─> quiet 5 V / 3.3 V sensor rails
```

The handheld battery is a removable 3S1P 21700 pack with BMS and fuel gauge. Robot input can be up to 33.6 V in the integration model, therefore the robot adapter includes a 24 V DC-DC stage before the handheld power input.

## 4. Safety architecture

Every heater is intended to have hardware thermal cutoff protection. Heater enable is additionally guarded by a watchdog/monostable arrangement and an independent over-temperature comparator/latch. The robot rear-connector e-stop loop directly cuts heater enable in hardware.

## 5. Robot adapter electronics

The robot integration CAD models:

- 33.6 → 24 V DC-DC conversion
- fuse
- e-stop relay
- e-stop button
- power/data cable between handheld rear connector and robot adapter
- service loop for payload tilt

The exact connector and current ratings remain items for verification.
