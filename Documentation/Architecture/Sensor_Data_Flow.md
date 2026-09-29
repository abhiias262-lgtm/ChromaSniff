# ChromaSniff — Sensor & Data Flow

## 1. Overall information path

```text
PHYSICAL SAMPLE
      │
      ├──────────────> Tier-1 ambient-air sensing
      │                 BME688 / SGP41 / TGS2600 / TGS2602 / SHT45
      │
      └──────────────> Controlled Tier-2 sample path
                         │
                         ▼
                    Chemical card
                         │
                         ├── Camera / RGB response
                         │
                         └── Downstream gas manifold
                              BME688 / TGS2620 / SHT45
                                      │
                                      ▼
                              Feature extraction
                                      │
                                      ▼
                              ML / sensor fusion
                                      │
                                      ▼
                           alert / retest / abstain
```

## 2. Tier-1

Tier-1 is physically separated from the sample-analysis chain. The sensor cell has its own top vent and fan. The sensors provide continuous ambient-air measurements used as the background/cueing channel.

The CAD does not define chemical identity from any single MOS sensor. The sensor outputs are treated as system evidence and environmental context.

## 3. Tier-2 card path

During vapour desorption, the collected material is flash-desorbed from the Tenax trap, cooled, passed over the chemical card and then enters the downstream manifold. During handheld SWV operation, a paired wet swab can also be used with the SPE/potentiostat channel.

## 4. Optical channel

The card is 40 × 25 mm and includes three ArUco markers. The camera is mounted above the card. The CAD validation requires the camera axis to be aligned with the card centre and reserves an optical keep-out around the imaging path.

The design also specifies lens-distortion calibration before ArUco registration and controlled LED/UV illumination. UV operation is lid-interlocked.

## 5. Downstream sensor channel

The manifold is a shared downstream sensing chamber rather than a standalone chemical identifier. It houses BME688 #2, TGS2620 and SHT45 #2. The resulting measurements provide additional evidence after the card response.

## 6. Environmental context

SHT45 sensors provide temperature/RH context. These measurements are part of the sensing architecture rather than direct target identification.

## 7. Data interpretation boundary

The CAD files specify the physical sensor and optical architecture. They do not, by themselves, establish analytical accuracy, chemical specificity, detection limits or field performance. Those require experimental validation using the project's defined test plan.
