# ChromaSniff — Gas Path Architecture

## 1. Physical flow

```text
SAMPLE
  │
  ▼
HEATED NOZZLE (~90 °C)
  │
  ▼
V1
  │
  ├── Vapour collection ──> Tenax trap (≤40 °C collection)
  │                          │
  │                          ▼
  │                     V2 heated
  │
  └── Controlled purge / desorption routing

DESORPTION
  │
  ▼
220–250 °C flash/desorption
  │
  ▼
COOLING COIL
  │
  ▼
CHEMICAL CARD
  │
  ▼
TIER-2 MANIFOLD
  │
  ▼
RESTRICTOR + CARBON FILTER
  │
  ▼
EXHAUST
```

## 2. Operating states

| State | Route | Robot |
|---|---|---|
| `TIER1_IDLE` | Tier-1 cell → fan → side vent | Yes |
| `VAPOUR_COLLECT` | Nozzle → V1 → Tenax trap → V2 → P1 → exhaust | Yes |
| `DRY_PURGE` | Scrubber → P2 → V3 → V1 → trap → V2 → P1 → exhaust | Yes |
| `VAPOUR_DESORB` | Scrubber → P2 → V3 → V1 → trap flash → V2 → cooling coil → card → manifold → exhaust | Yes |
| `SWAB_DESORB` | Scrubber → P2 → V3 → swab chamber → cooling coil → card → manifold → exhaust | No |
| `CLEAN_COOL` | Scrubber → P2 → V3 → swab/trap → coil → card → manifold → exhaust | Yes |

## 3. Important gas-path rules

- Tenax trap is both the vapour collector and vapour desorber.
- V2 is the only valve located in the hot path.
- Swab chamber and V2 outlets join before the cooling coil.
- The card is downstream of the cooling section.
- No silicone tubing is specified for the analyte path.
- Cool-side tubing is planned as PTFE/FEP; hot sections use passivated stainless steel where applicable, subject to verification.
- Exhaust is carbon-filtered and positioned away from the nozzle and Tier-1 intake.

## 4. Pumps and valves

- **P1:** collection pump.
- **P2:** zero-air/purge pump.
- **V1:** sample/zero-air selection.
- **V2:** heated trap-outlet routing.
- **V3:** purge routing between trap path and swab chamber.
- **Scrubber:** serviceable zero-air scrubber.

## 5. CAD validation

The handheld script validates the existence of each route node and calculates a schematic centre-to-centre route length. Final physical tubing must still be routed with real bend radii and bulkhead pass-throughs before fabrication.
