# ChromaSniff_FreeCAD_Skeleton_v1_1.py
#
# Pistol-grip handheld + detachable robot payload — parametric CAD skeleton.
#
# HOW TO USE
#   In FreeCAD (0.21 or 1.0): Macro > Macros... > run this file.
#     - Builds document "ChromaSniff_V1_1" with:
#         CS_MasterParameters  spreadsheet: every envelope's position/size + global params
#         CS_DesignNotes       spreadsheet: design rules and open items
#         CS_ValidationReport  spreadsheet: results of the automatic layout checks
#       and one Part::Box per envelope, bound to the spreadsheet by expressions.
#     - Edit numbers in CS_MasterParameters, press Recompute, then type
#       run_checks() in the Python console to re-validate and redraw gas routes.
#     - Switch configuration: set Config_Robot = 1 (robot) or 0 (handheld), run_checks().
#   Without FreeCAD (plain Python 3):  python3 ChromaSniff_FreeCAD_Skeleton_v1_1.py
#     - Runs the same layout checks on the table below for BOTH configurations.
#
# COORDINATES (right-handed, mm)
#   X = width (+X = user's right)   Y = depth (+Y = forward, toward nozzle)
#   Z = height (+Z = up)            Origin: rear face (Y=0), barrel bottom (Z=0), centreline (X=0)
#
# ALL DIMENSIONS ARE PLACEHOLDER ENVELOPES. Candidate parts are listed per item
# but none is purchased/frozen. Replace every envelope with datasheet/STEP geometry.

import math
import os

try:
    import FreeCAD as App
    import Part
    HAVE_FC = True
except ImportError:
    HAVE_FC = False

DOC_NAME = "ChromaSniff_V1_1"
SHEET = "CS_MasterParameters"

# ---------------------------------------------------------------------------
# Global parameters (CS_MasterParameters, top section)
# ---------------------------------------------------------------------------
GLOBALS = [
    # alias, value, note
    ("Config_Robot", 0, "0 = HANDHELD (grip + battery), 1 = ROBOT (adapter plate, robot power)"),
    ("Wall_T", 3, "Enclosure wall thickness (placeholder)"),
    ("Desorb_Temp_Max", 250, "degC - Tenax trap flash / swab plate (documented 220-250)"),
    ("Nozzle_Temp", 90, "degC - heated nozzle (documented)"),
    ("Card_Temp_Max", 40, "degC - card surface limit (documented)"),
    ("Card_W", 25, "mm - matches chromasniff_registration.py (40 x 25 card)"),
    ("Card_L", 40, "mm"),
    ("Lens_HFOV_deg", 90, "Camera lens horizontal FOV - PLACEHOLDER, set from chosen M12 lens"),
    ("FOV_Margin", 1.2, "Required field = card length x margin"),
    ("Min_Card_Bulkhead_Gap", 15, "mm - card holder to thermal bulkhead (validate by thermal test)"),
    ("Min_Elec_Hot_Clearance", 40, "mm - electronics to hot keep-out"),
    ("Min_Exhaust_Tier1_Dist", 40, "mm - exhaust port to Tier-1 intake (validate by smoke test)"),
    ("Min_Exhaust_Nozzle_Dist", 100, "mm - exhaust port to nozzle (avoid re-sampling own exhaust)"),
    ("Max_Nozzle_Protrusion", 40, "mm beyond front face"),
    ("Max_Connector_Protrusion", 25, "mm beyond rear face"),
    ("Max_Minor_Protrusion", 10, "mm - exhaust port, SPE tail, USB-C"),
]

# ---------------------------------------------------------------------------
# Envelopes
#   (name, group, class, parent, x0, y0, z0, dx, dy, dz, config, label, candidate)
# class:  HOT (>=200 degC) | WARM (60-120 degC) | INTER (cooling path) | COOL
#         INSUL (thermal barrier) | ENV (reference envelope) | ACCESS (user/tool volume)
#         KEEPOUT_HOT | KEEPOUT_OPT
# config: B = both, H = handheld only, R = robot only
# ---------------------------------------------------------------------------
I = [
 # ---- master ----
 ("Barrel_Envelope", "00_MASTER", "ENV", None, -35, 0, 0, 70, 250, 88, "B",
  "Barrel outer envelope", "Enclosure: ASA/PETG proto -> PA12 SLS/MJF V2"),
 # ---- hot zone (front) ----
 ("Nozzle", "02_GAS_PATH", "WARM", None, 4, 247, 10, 16, 38, 16, "B",
  "Heated sampling nozzle 90 C + guard", "SS/PTFE-lined nozzle, cartridge or wire heater"),
 ("Valve_V1", "02_GAS_PATH", "WARM", None, 4, 232, 10, 16, 14, 16, "B",
  "V1 sample / zero-air select", "3-way mini solenoid, PTFE/FKM wetted"),
 ("Tenax_Trap", "02_GAS_PATH", "HOT", None, 4, 200, 8, 26, 30, 26, "B",
  "Tenax TA trap = vapour desorber (flash 220-250 C)", "1/4in SS tube + Tenax TA 60/80 + heater + K-TC"),
 ("Valve_V2_Heated", "02_GAS_PATH", "HOT", None, 4, 190, 10, 16, 9, 16, "B",
  "V2 heated, trap outlet: exhaust vs card", "PTFE/PEEK-wetted 3-way, rated >=100 C, heated"),
 ("Swab_Chamber", "02_GAS_PATH", "HOT", None, -31, 195, 8, 27, 50, 42, "B",
  "Swab chamber + 220-250 C plate (swab desorber)", "Al block + 12 V cartridge heater + K-TC"),
 ("Hot_Keepout", "03_THERMAL", "KEEPOUT_HOT", None, -32, 190, 3, 64, 57, 82, "B",
  "HOT ZONE KEEP-OUT", "-"),
 ("Heat_Shield", "03_THERMAL", "INSUL", None, -32, 190, 60, 64, 57, 2, "B",
  "Top heat shield (perforated)", "Polished Al sheet"),
 ("Trap_Fan", "03_THERMAL", "WARM", None, 4, 205, 72, 26, 26, 10, "B",
  "Trap cooling fan (pulls through top hot vent)", "25 mm fan, high-temp rated - VERIFY rating"),
 ("Thermal_Bulkhead", "03_THERMAL", "INSUL", None, -32, 183, 3, 64, 6, 82, "B",
  "Thermal bulkhead with gas pass-throughs", "PEEK or glass-mica board + aerogel blanket"),
 # ---- intermediate ----
 ("Cooling_Coil", "02_GAS_PATH", "INTER", None, 3, 150, 6, 28, 32, 28, "B",
  "Cooling length (card inlet <= 40 C)", "PTFE/FEP coil or finned SS tube"),
 ("Scrubber", "02_GAS_PATH", "COOL", None, -31, 150, 6, 28, 32, 28, "B",
  "Zero-air scrubber (carbon + silica), serviceable", "Refillable PP cartridge"),
 # ---- card / optics ----
 ("Card_Holder", "04_CARD_OPTICS", "COOL", None, -25, 120, 38, 32, 48, 12, "B",
  "Card holder + flow cell + seal (left-side door)", "Al or PEEK frame, FKM gasket, keyed"),
 ("Card", "04_CARD_OPTICS", "COOL", "Card_Holder", -21.5, 124, 44, 25, 40, 1, "B",
  "Chemical card 40 x 25 mm, 3 ArUco", "PVDF on rigid carrier"),
 ("Optical_Window", "04_CARD_OPTICS", "COOL", None, -24, 121, 50, 30, 46, 2, "B",
  "Optical window", "Borosilicate 2 mm, anti-fog"),
 ("LED_Ring", "04_CARD_OPTICS", "COOL", None, -24, 121, 60, 30, 46, 2, "B",
  "5000 K CRI>=90 LEDs + 365 nm UV (lid-interlocked)", "Custom ring PCB with aperture"),
 ("Camera_Mount", "04_CARD_OPTICS", "COOL", None, -26, 128, 66, 34, 32, 6, "B",
  "Rigid camera mount (aperture)", "Machined Al / printed with inserts"),
 ("Camera", "04_CARD_OPTICS", "COOL", None, -21.5, 132, 72, 25, 24, 12, "B",
  "Camera (short working distance)", "M12-mount IMX219/IMX708 module for Pi + wide M12 lens [verify]"),
 ("Optical_Keepout", "04_CARD_OPTICS", "KEEPOUT_OPT", None, -23, 122, 52, 28, 44, 20, "B",
  "Optical path keep-out", "-"),
 ("Valve_V3", "02_GAS_PATH", "COOL", None, 9, 122, 38, 20, 14, 16, "B",
  "V3 purge route: trap path vs swab chamber", "3-way mini solenoid"),
 # ---- downstream ----
 ("Manifold", "05_SENSORS", "COOL", None, -26, 95, 38, 30, 23, 24, "B",
  "Tier-2 downstream sensor manifold", "PTFE/Al manifold, O-ring lid"),
 ("Manifold_SensorPCB", "05_SENSORS", "COOL", "Manifold", -25, 96, 39, 28, 21, 2, "B",
  "Manifold sensor PCB", "Custom PCB"),
 ("BME688_02", "05_SENSORS", "COOL", "Manifold", -23, 98, 41, 3, 3, 1, "B", "BME688 #2", "Bosch BME688"),
 ("TGS2620", "05_SENSORS", "COOL", "Manifold", -18, 98, 41, 10, 10, 10, "B", "TGS2620", "Figaro TGS2620"),
 ("SHT45_02", "05_SENSORS", "COOL", "Manifold", -6, 98, 41, 2, 2, 1, "B", "SHT45 #2", "Sensirion SHT45"),
 ("Restrictor_Exhaust_Filter", "02_GAS_PATH", "COOL", None, 8, 95, 38, 23, 23, 17, "B",
  "Restrictor + carbon exhaust filter", "Orifice + small carbon cartridge"),
 ("Exhaust_Port", "02_GAS_PATH", "COOL", None, 31, 100, 40, 6, 12, 12, "B",
  "Exhaust port (right side, angled down)", "-"),
 ("Pump_P1", "02_GAS_PATH", "COOL", None, 3, 110, 8, 28, 38, 27, "B",
  "P1 collect pump", "12 V brushless micro diaphragm 0.3-1 L/min [verify]"),
 ("Pump_P2", "02_GAS_PATH", "COOL", None, -31, 110, 8, 28, 38, 27, "B",
  "P2 zero-air / purge pump", "12 V brushless micro diaphragm [verify]"),
 # ---- Tier-1 ----
 ("Tier1_Cell", "05_SENSORS", "COOL", None, -31, 62, 58, 29, 30, 27, "B",
  "Tier-1 air cell (top vent, own fan)", "Printed cell, PTFE-lined"),
 ("Tier1_SensorPCB", "05_SENSORS", "COOL", "Tier1_Cell", -30, 63, 59, 27, 28, 2, "B", "Tier-1 sensor PCB", "Custom PCB"),
 ("TGS2600", "05_SENSORS", "COOL", "Tier1_Cell", -28, 65, 61, 10, 10, 10, "B", "TGS2600", "Figaro TGS2600"),
 ("TGS2602", "05_SENSORS", "COOL", "Tier1_Cell", -16, 65, 61, 10, 10, 10, "B", "TGS2602", "Figaro TGS2602"),
 ("BME688_01", "05_SENSORS", "COOL", "Tier1_Cell", -28, 80, 61, 3, 3, 1, "B", "BME688 #1", "Bosch BME688"),
 ("SGP41", "05_SENSORS", "COOL", "Tier1_Cell", -22, 80, 61, 3, 3, 1, "B", "SGP41", "Sensirion SGP41"),
 ("SHT45_01", "05_SENSORS", "COOL", "Tier1_Cell", -16, 80, 61, 2, 2, 1, "B", "SHT45 #1", "Sensirion SHT45"),
 ("Tier1_Fan", "05_SENSORS", "COOL", "Tier1_Cell", -29, 64, 74, 25, 25, 10, "B", "Tier-1 fan", "25 mm 5 V fan"),
 # ---- electrochemical (paired wet swab) ----
 ("SWV_Module", "05_SENSORS", "COOL", None, 4, 62, 38, 27, 30, 18, "B",
  "Potentiostat + SPE edge connector", "PalmSens EmStat Pico or AD5941 design [verify]"),
 ("SPE_Strip", "05_SENSORS", "COOL", None, 8, 72, 46, 34, 10, 1, "B",
  "Screen-printed electrode (right-side slot)", "DropSens DRP-110 format [verify dims]"),
 # ---- electronics ----
 ("RPi5", "06_ELECTRONICS", "COOL", None, -28, 20, 8, 56, 85, 22, "B",
  "Raspberry Pi 5 + active cooler", "Raspberry Pi 5 (V2: Compute Module 5 on carrier)"),
 ("Main_Control_PCB", "06_ELECTRONICS", "COOL", None, -30, 12, 38, 60, 48, 10, "B",
  "Control PCB: ESP32-S3, ADCs, drivers, heater watchdog, ATECC608B", "ESP32-S3-WROOM-1-N8R8"),
 ("Power_Board", "07_POWER", "COOL", None, -30, 12, 51, 60, 48, 10, "B",
  "Power: ideal-diode OR, 9-28 V buck-boost -> 12 V, 5 V/5 A", "Custom or module-based [verify]"),
 ("GNSS_LoRa", "06_ELECTRONICS", "COOL", None, 2, 62, 70, 28, 30, 12, "B",
  "GNSS + LoRa (patch antenna under top skin)", "u-blox NEO-M9N + RFM95W 868 [verify]"),
 ("Display", "06_ELECTRONICS", "COOL", None, -31.5, 1, 40, 63, 6, 44, "B",
  "Rear display (sunlight-readable)", "Sharp LS027B7DH01 2.7in memory LCD [verify dims]"),
 ("USB_C_Service", "06_ELECTRONICS", "COOL", None, 18, -2, 10, 12, 15, 8, "B",
  "USB-C service/data port", "Panel-mount USB-C, IP-rated"),
 # ---- payload interface / power ----
 ("Rear_Connector", "08_PAYLOAD_INTERFACE", "COOL", None, -14, -22, 6, 28, 40, 26, "B",
  "Rear payload connector: 12-24 V, e-stop loop, RS-485/CAN", "GX16-8 (proto) -> M12 8-pin A-coded (V2) [verify]"),
 ("Dovetail_Rail", "08_PAYLOAD_INTERFACE", "COOL", None, -19, 50, -6, 38, 80, 6, "B",
  "38 mm Arca-type dovetail (grip AND robot mount)", "Arca-Swiss-compatible profile [verify]"),
 ("Pogo_Contacts", "07_POWER", "COOL", None, -10, 70, 0, 20, 16, 7, "B",
  "Grip-to-barrel battery contacts", "Spring-pin block, >=3 pins per rail [verify current]"),
 ("Grip_Module", "08_PAYLOAD_INTERFACE", "COOL", None, -22, 60, -121, 44, 50, 115, "H",
  "Detachable pistol grip (clamps dovetail)", "Printed shell + TPU overmould"),
 ("Harness_Grip", "09_WIRING", "COOL", "Grip_Module", -15, 70, -110, 30, 30, 100, "H",
  "Grip wiring channel", "-"),
 ("Trigger", "06_ELECTRONICS", "COOL", None, -5, 110, -40, 10, 8, 22, "H",
  "Trigger = start test", "Sealed momentary switch"),
 ("Battery_Base", "07_POWER", "COOL", None, -35, 45, -151, 70, 82, 30, "H",
  "Battery dock (bottom of grip)", "-"),
 ("Battery_Pack", "07_POWER", "COOL", "Battery_Base", -33, 48, -148, 66, 78, 24, "H",
  "Removable 3S1P 21700 pack + BMS + fuel gauge", "3x 21700 (e.g. Samsung 50S / Molicel P45B) [verify]"),
 ("Robot_Adapter", "08_PAYLOAD_INTERFACE", "COOL", None, -40, 45, -26, 80, 85, 20, "R",
  "Robot adapter: dovetail clamp + 0-30 deg tilt", "Arca clamp + Al bracket"),
 # ---- access volumes (must stay clear) ----
 ("Access_Card_Door", "10_SERVICE_ACCESS", "ACCESS", None, -60, 118, 36, 25, 52, 16, "B", "Card door finger access (left)", "-"),
 ("Access_Swab_Port", "10_SERVICE_ACCESS", "ACCESS", None, -60, 203, 18, 25, 34, 22, "B", "Swab insertion (left, front)", "-"),
 ("Access_SPE_Slot", "10_SERVICE_ACCESS", "ACCESS", None, 35, 66, 40, 25, 22, 14, "B", "SPE insertion (right)", "-"),
 ("Access_Service_Hatch", "10_SERVICE_ACCESS", "ACCESS", None, -30, 132, -30, 60, 50, 30, "B", "Bottom hatch: pumps, scrubber, coil", "-"),
 ("Access_Battery_Swap", "10_SERVICE_ACCESS", "ACCESS", None, -35, 127, -151, 70, 40, 30, "H", "Battery slides out forward", "-"),
]

PHYS = {"HOT", "WARM", "INTER", "COOL", "INSUL"}
EXTERNAL = {"Grip_Module", "Harness_Grip", "Trigger", "Battery_Base", "Battery_Pack",
            "Dovetail_Rail", "Robot_Adapter"}          # outside the barrel by design
PROTRUDE = {"Nozzle": ("+Y", "Max_Nozzle_Protrusion"),
            "Rear_Connector": ("-Y", "Max_Connector_Protrusion"),
            "USB_C_Service": ("-Y", "Max_Minor_Protrusion"),
            "Exhaust_Port": ("+X", "Max_Minor_Protrusion"),
            "SPE_Strip": ("+X", "Max_Minor_Protrusion")}
ALLOWED_OVERLAP = {frozenset(p) for p in [
    ("Optical_Keepout", "LED_Ring"), ("Optical_Keepout", "Camera_Mount"),  # both have apertures
    ("Access_SPE_Slot", "SPE_Strip"), ("SPE_Strip", "SWV_Module"),           # strip plugs into module
]}
ELECTRONICS = {"RPi5", "Main_Control_PCB", "Power_Board", "GNSS_LoRa", "Display", "SWV_Module",
               "Battery_Pack", "Battery_Base"}

# Gas routes per operating state (node order = flow direction)
ROUTES = {
    "TIER1_IDLE":     ["Tier1_Cell", "Tier1_Fan"],
    "VAPOUR_COLLECT": ["Nozzle", "Valve_V1", "Tenax_Trap", "Valve_V2_Heated", "Pump_P1", "Exhaust_Port"],
    "DRY_PURGE":      ["Scrubber", "Pump_P2", "Valve_V3", "Valve_V1", "Tenax_Trap", "Valve_V2_Heated",
                       "Pump_P1", "Exhaust_Port"],
    "VAPOUR_DESORB":  ["Scrubber", "Pump_P2", "Valve_V3", "Valve_V1", "Tenax_Trap", "Valve_V2_Heated",
                       "Cooling_Coil", "Card_Holder", "Manifold", "Restrictor_Exhaust_Filter", "Exhaust_Port"],
    "SWAB_DESORB":    ["Scrubber", "Pump_P2", "Valve_V3", "Swab_Chamber", "Cooling_Coil", "Card_Holder",
                       "Manifold", "Restrictor_Exhaust_Filter", "Exhaust_Port"],
    "CLEAN_COOL":     ["Scrubber", "Pump_P2", "Valve_V3", "Swab_Chamber", "Cooling_Coil", "Card_Holder",
                       "Manifold", "Restrictor_Exhaust_Filter", "Exhaust_Port"],
}
ROBOT_MODES = ["TIER1_IDLE", "VAPOUR_COLLECT", "DRY_PURGE", "VAPOUR_DESORB", "CLEAN_COOL"]  # no swab on robot

NOTES = [
    ("R01", "Electronics, battery and card never inside the HOT keep-out."),
    ("R02", "Card only after the cooling length; card surface <= 40 C (validate by thermocouple test)."),
    ("R03", "Tenax trap IS the vapour desorber; swab plate is the second hot element. Both inside the keep-out."),
    ("R04", "Only V2 sits in the hot path: PTFE/PEEK-wetted, heated, rated >=100 C."),
    ("R05", "Card removable via left door without opening the enclosure; keyed, sealed flow cell."),
    ("R06", "Camera sees full card + 3 ArUco markers; wide M12 lens needs a lens-distortion calibration step."),
    ("R07", "Exhaust (right, angled down, carbon-filtered) away from nozzle, Tier-1 intake and user face."),
    ("R08", "Hardware thermal cutoffs + heater-enable watchdog on every heater, independent of software."),
    ("R09", "One payload interface: 38 mm dovetail carries the grip (handheld) or robot adapter (robot)."),
    ("R10", "Robot mode: robot power via rear connector; Tier-1 continuous + vapour mode with a pre-loaded card. No swab on robot."),
    ("R11", "Hardware e-stop loop in rear connector cuts heater enable directly."),
    ("R12", "All dimensions are placeholders until parts are selected; replace boxes with STEP models."),
    ("OPEN", "PID not reserved in the V1 envelope (no room); add as side-port module in V2 if needed."),
    ("OPEN", "Trap fan sees warm air above the heat shield: confirm fan temperature rating by test."),
    ("OPEN", "Tier-1 top vent: confirm no self-sampling of exhaust with a smoke/tracer test."),
]


# ---------------------------------------------------------------------------
# Geometry helpers (work with or without FreeCAD); bbox = (x0,y0,z0,x1,y1,z1)
# ---------------------------------------------------------------------------
def bbox_of(row):
    _, _, _, _, x, y, z, dx, dy, dz = row[:10]
    return (x, y, z, x + dx, y + dy, z + dz)


def overlap(a, b, tol=0.01):
    return all(a[i] < b[i + 3] - tol and b[i] < a[i + 3] - tol for i in range(3))


def inside(a, b, tol=0.01):
    return all(a[i] >= b[i] - tol and a[i + 3] <= b[i + 3] + tol for i in range(3))


def centre(b):
    return tuple((b[i] + b[i + 3]) / 2 for i in range(3))


def gap(a, b):
    d = [max(0.0, b[i] - a[i + 3], a[i] - b[i + 3]) for i in range(3)]
    return math.sqrt(sum(v * v for v in d))


# ---------------------------------------------------------------------------
# Validation. items = {name: (bbox, class, parent, config)}, P = globals dict
# ---------------------------------------------------------------------------
def validate(items, P, robot):
    res = []

    def rec(check, ok, detail):
        res.append((check, "PASS" if ok else "FAIL", detail))

    cfg = "R" if robot else "H"
    act = {n: v for n, v in items.items() if v[3] in ("B", cfg)}
    phys = {n: v for n, v in act.items() if v[1] in PHYS}
    barrel = act["Barrel_Envelope"][0]

    # 1. envelope / allowed protrusions
    for n, (b, c, par, _) in phys.items():
        if n in EXTERNAL or par in EXTERNAL:
            continue
        if n in PROTRUDE:
            axis, alias = PROTRUDE[n]
            lim = P[alias]
            k = "XYZ".index(axis[1])
            ext = b[k + 3] - barrel[k + 3] if axis[0] == "+" else barrel[k] - b[k]
            ok_other = all(b[i] >= barrel[i] - 0.01 and b[i + 3] <= barrel[i + 3] + 0.01
                           for i in range(3) if i != k)
            rec("Envelope", ok_other and ext <= lim,
                f"{n}: protrudes {max(ext, 0):.1f} mm {axis} (limit {lim})")
        elif not inside(b, barrel):
            rec("Envelope", False, f"{n} outside barrel envelope")
    # 2. collisions: top-level vs top-level, and siblings under the same parent
    names = sorted(phys)
    n_coll = 0
    for i, a in enumerate(names):
        for bn in names[i + 1:]:
            A, B = phys[a], phys[bn]
            if A[2] != B[2]:            # different parents: parent/child or cousins -> skip
                continue
            if frozenset((a, bn)) in ALLOWED_OVERLAP:
                continue
            if overlap(A[0], B[0]):
                n_coll += 1
                rec("Collision", False, f"{a} x {bn}")
    rec("Collision", n_coll == 0, f"{n_coll} collisions among {len(names)} physical envelopes")
    # 3. containment of children
    for n, (b, c, par, _) in act.items():
        if par and par in act:
            rec("Containment", inside(b, act[par][0]), f"{n} inside {par}")
    # 4. thermal
    hk = act["Hot_Keepout"][0]
    for n, (b, c, par, _) in phys.items():
        if c in ("COOL", "INTER") and overlap(b, hk):
            rec("Hot keep-out", False, f"{n} ({c}) intrudes hot keep-out")
        if c == "HOT":
            rec("Hot keep-out", inside(b, hk), f"{n} (HOT) contained in keep-out")
    for n in ELECTRONICS:
        if n in act:
            g = gap(act[n][0], hk)
            rec("Electronics clearance", g >= P["Min_Elec_Hot_Clearance"],
                f"{n}: {g:.0f} mm to hot keep-out (min {P['Min_Elec_Hot_Clearance']:.0f})")
    gcb = gap(act["Card_Holder"][0], act["Thermal_Bulkhead"][0])
    rec("Card thermal gap", gcb >= P["Min_Card_Bulkhead_Gap"],
        f"card holder to bulkhead {gcb:.0f} mm (min {P['Min_Card_Bulkhead_Gap']:.0f}) - thermal test required")
    # 5. optics
    card, cam = act["Card"][0], act["Camera"][0]
    cc, kc = centre(card), centre(cam)
    off = math.hypot(cc[0] - kc[0], cc[1] - kc[1])
    rec("Optics", off <= 1.0, f"camera axis offset from card centre {off:.2f} mm (max 1.0)")
    wd = cam[2] - card[5]
    need = 2 * math.degrees(math.atan(P["Card_L"] * P["FOV_Margin"] / 2 / wd)) if wd > 0 else 999
    rec("Optics", need <= P["Lens_HFOV_deg"],
        f"working distance {wd:.0f} mm needs HFOV >= {need:.0f} deg (lens {P['Lens_HFOV_deg']:.0f})")
    ok_card = (abs((card[3] - card[0]) - P["Card_W"]) < 0.1 and abs((card[4] - card[1]) - P["Card_L"]) < 0.1)
    rec("Optics", ok_card, "card envelope matches Card_W x Card_L (registration code)")
    ko = act["Optical_Keepout"][0]
    rec("Optics", ko[0] <= card[0] and ko[3] >= card[3] and ko[1] <= card[1] and ko[4] >= card[4],
        "optical keep-out footprint covers the card")
    for n, (b, c, par, _) in phys.items():
        if frozenset((n, "Optical_Keepout")) not in ALLOWED_OVERLAP and overlap(b, ko):
            rec("Optics", False, f"{n} blocks the optical path")
    # 6. access volumes
    for n, (b, c, par, _) in act.items():
        if c != "ACCESS":
            continue
        hits = [m for m, v in phys.items() if overlap(b, v[0]) and frozenset((n, m)) not in ALLOWED_OVERLAP]
        rec("Access", not hits, f"{n} clear" + (f" - blocked by {hits}" if hits else ""))
    # 7. exhaust placement
    t1 = act["Tier1_Cell"][0]
    intake = ((t1[0] + t1[3]) / 2, (t1[1] + t1[4]) / 2, t1[5])
    ex = centre(act["Exhaust_Port"][0])
    d = math.dist(intake, ex)
    rec("Exhaust", d >= P["Min_Exhaust_Tier1_Dist"], f"exhaust to Tier-1 intake {d:.0f} mm - smoke test required")
    dn = math.dist(centre(act["Nozzle"][0]), ex)
    rec("Exhaust", dn >= P["Min_Exhaust_Nozzle_Dist"], f"exhaust to nozzle {dn:.0f} mm")
    # 8. gas routes
    for mode, route in ROUTES.items():
        if robot and mode not in ROBOT_MODES:
            continue
        missing = [n for n in route if n not in act]
        L = sum(math.dist(centre(act[route[i]][0]), centre(act[route[i + 1]][0]))
                for i in range(len(route) - 1)) if not missing else 0
        rec("Gas route", not missing, f"{mode}: {' > '.join(route)} (~{L:.0f} mm centre-to-centre)"
            + (f" MISSING {missing}" if missing else ""))
    return res


def table_items():
    return {r[0]: (bbox_of(r), r[2], r[3], r[10]) for r in I}


def print_report(res, title):
    print("\n=== " + title + " ===")
    fails = [r for r in res if r[1] == "FAIL"]
    for c, s, d in res:
        if s == "FAIL" or c in ("Gas route", "Optics", "Card thermal gap", "Exhaust", "Collision"):
            print(f"[{s}] {c}: {d}")
    print(f"--> {len(res) - len(fails)} passed, {len(fails)} failed")
    return fails


# ---------------------------------------------------------------------------
# FreeCAD build
# ---------------------------------------------------------------------------
if HAVE_FC:
    COLORS = {"HOT": (0.85, 0.2, 0.1), "WARM": (0.95, 0.55, 0.1), "INTER": (0.95, 0.85, 0.3),
              "COOL": (0.3, 0.55, 0.85), "INSUL": (0.6, 0.6, 0.6), "ENV": (0.8, 0.8, 0.8),
              "ACCESS": (0.3, 0.8, 0.4), "KEEPOUT_HOT": (1.0, 0.0, 0.0), "KEEPOUT_OPT": (0.6, 0.3, 0.9)}
    TRANSP = {"ENV": 92, "ACCESS": 80, "KEEPOUT_HOT": 85, "KEEPOUT_OPT": 85}

    def _fill_sheet(sheet):
        sheet.set("A1", "Alias"); sheet.set("B1", "Value"); sheet.set("C1", "Note")
        r = 1
        for alias, val, note in GLOBALS:
            r += 1
            sheet.set(f"A{r}", alias); sheet.set(f"B{r}", f"={val}"); sheet.set(f"C{r}", note)
            sheet.setAlias(f"B{r}", alias)
        r += 2
        for col, h in zip("ABCDEFGHIJ", ("Envelope", "X0", "Y0", "Z0", "DX", "DY", "DZ",
                                         "Class", "Config", "Candidate part (NOT frozen)")):
            sheet.set(f"{col}{r}", h)
        for row in I:
            r += 1
            name = row[0]
            sheet.set(f"A{r}", name)
            for col, val, suf in zip("BCDEFG", row[4:10], ("X0", "Y0", "Z0", "DX", "DY", "DZ")):
                sheet.set(f"{col}{r}", f"={val}")
                sheet.setAlias(f"{col}{r}", f"{name}_{suf}")
            sheet.set(f"H{r}", row[2]); sheet.set(f"I{r}", row[10]); sheet.set(f"J{r}", row[12])

    def build():
        if DOC_NAME in App.listDocuments():
            App.closeDocument(DOC_NAME)
        doc = App.newDocument(DOC_NAME)
        _fill_sheet(doc.addObject("Spreadsheet::Sheet", SHEET))
        notes = doc.addObject("Spreadsheet::Sheet", "CS_DesignNotes")
        notes.set("A1", "ID"); notes.set("B1", "Rule / open item")
        for k, (rid, txt) in enumerate(NOTES, start=2):
            notes.set(f"A{k}", rid); notes.set(f"B{k}", txt)
        doc.recompute()
        groups = {}
        for g in sorted({row[1] for row in I} | {"09_WIRING", "11_VALIDATION"}):
            grp = doc.addObject("App::DocumentObjectGroup", "G" + g)
            grp.Label = g
            groups[g] = grp
        groups["00_MASTER"].addObject(doc.getObject(SHEET))
        groups["00_MASTER"].addObject(notes)
        for row in I:
            name, g, cls, parent = row[:4]
            obj = doc.addObject("Part::Box", "CS_" + name)
            obj.Label = f"CS_{name} - {row[11]}"
            for prop, suf in (("Length", "DX"), ("Width", "DY"), ("Height", "DZ")):
                obj.setExpression(prop, f"{SHEET}.{name}_{suf}")
            for ax, suf in (("x", "X0"), ("y", "Y0"), ("z", "Z0")):
                obj.setExpression(f"Placement.Base.{ax}", f"{SHEET}.{name}_{suf}")
            for pname, val in (("CS_Class", cls), ("CS_Parent", parent or ""), ("CS_Config", row[10]),
                               ("CS_Candidate", row[12]),
                               ("CS_Status", "PLACEHOLDER ENVELOPE - replace with datasheet/STEP geometry")):
                obj.addProperty("App::PropertyString", pname, "ChromaSniff")
                setattr(obj, pname, val)
            groups[g].addObject(obj)
            if App.GuiUp:
                obj.ViewObject.ShapeColor = COLORS.get(cls, (0.5, 0.5, 0.5))
                obj.ViewObject.Transparency = TRANSP.get(cls, 30)
        doc.recompute()
        return doc

    def _params(doc):
        s = doc.getObject(SHEET)
        return {a: float(s.get(a)) for a, _, _ in GLOBALS}

    def apply_config(doc):
        robot = _params(doc)["Config_Robot"] >= 0.5
        cfg = "R" if robot else "H"
        if App.GuiUp:
            for o in doc.Objects:
                if hasattr(o, "CS_Config"):
                    o.ViewObject.Visibility = o.CS_Config in ("B", cfg)
        return robot

    def live_items(doc):
        out = {}
        for o in doc.Objects:
            if hasattr(o, "CS_Class"):
                bb = o.Shape.BoundBox
                out[o.Name[3:]] = ((bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax),
                                   o.CS_Class, o.CS_Parent or None, o.CS_Config)
        return out

    def draw_routes(doc, items, robot):
        grp = doc.getObject("G11_VALIDATION")
        for o in list(doc.Objects):
            if o.Name.startswith("Route_"):
                doc.removeObject(o.Name)
        for mode, route in ROUTES.items():
            if robot and mode not in ROBOT_MODES:
                continue
            pts = [App.Vector(*centre(items[n][0])) for n in route if n in items]
            if len(pts) > 1:
                w = doc.addObject("Part::Feature", "Route_" + mode)
                w.Shape = Part.makePolygon(pts)
                w.Label = f"Gas route {mode} (schematic, centre-to-centre)"
                grp.addObject(w)
                if App.GuiUp:
                    w.ViewObject.LineWidth = 3
                    w.ViewObject.LineColor = (0.1, 0.7, 0.3) if "SWAB" in mode else (0.1, 0.4, 0.9)

    def run_checks(doc=None):
        doc = doc or App.ActiveDocument
        doc.recompute()
        robot = apply_config(doc)
        items = live_items(doc)
        res = validate(items, _params(doc), robot)
        fails = print_report(res, "ChromaSniff layout checks - " + ("ROBOT" if robot else "HANDHELD"))
        rep = doc.getObject("CS_ValidationReport") or doc.addObject("Spreadsheet::Sheet", "CS_ValidationReport")
        rep.clearAll()
        rep.set("A1", "Check"); rep.set("B1", "Result"); rep.set("C1", "Detail")
        for k, (c, s, d) in enumerate(res, start=2):
            rep.set(f"A{k}", c); rep.set(f"B{k}", s); rep.set(f"C{k}", "'" + d)
        doc.getObject("G11_VALIDATION").addObject(rep)
        draw_routes(doc, items, robot)
        doc.recompute()
        return fails

    _doc = build()
    run_checks(_doc)
    _path = os.path.join(os.path.expanduser("~"), "ChromaSniff_V1_1_Skeleton.FCStd")
    try:
        _doc.saveAs(_path)
        print("Saved:", _path)
    except Exception as e:  # report, don't hide
        print("WARNING: could not save to", _path, "->", e)
    if App.GuiUp:
        import FreeCADGui as Gui
        Gui.activeDocument().activeView().viewIsometric()
        Gui.SendMsgToActiveView("ViewFit")
    print("All envelopes are PLACEHOLDERS. Edit CS_MasterParameters, recompute, then run_checks().")

elif __name__ == "__main__":
    P = {a: v for a, v, _ in GLOBALS}
    total_fail = 0
    for robot in (False, True):
        total_fail += len(print_report(validate(table_items(), P, robot),
                                       "Dry run - " + ("ROBOT" if robot else "HANDHELD")))
    raise SystemExit(1 if total_fail else 0)
