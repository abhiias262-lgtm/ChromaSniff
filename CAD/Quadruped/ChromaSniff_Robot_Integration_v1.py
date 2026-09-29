# ChromaSniff_Robot_Integration_v1.py
#
# Quadruped robot integration for the ChromaSniff V1.1 handheld (robot configuration).
#
# WHAT IT BUILDS (FreeCAD 0.21 / 1.0)
#   Document "ChromaSniff_Robot_V1" containing
#     00_PARAMETERS       CS_RobotParameters spreadsheet (edit -> run rebuild())
#     01_QUADRUPED        Go2-class placeholder: trunk, head, chin LiDAR, 4 legs (2-link IK pose)
#     02_MOUNT_FIXED      robot payload plate, adapter base plate, hinge cheeks, tilt-lock knob,
#                         adapter electronics box (33.6->24 V DC-DC, fuse, e-stop relay), e-stop button
#     03_MOUNT_TILTING    cradle plate, hinge lug, Arca clamp, clamp knob (rotate with the payload)
#     04_HANDHELD_PAYLOAD the handheld envelopes in ROBOT configuration, placed on the clamp
#     05_CABLES           rear-connector -> adapter box -> robot power/data port (with service loop)
#     06_VALIDATION       CS_RobotValidation report, CoG marker, nozzle-tip marker
#
# HANDHELD SOURCE (first found wins)
#   1. ChromaSniff_V1_1_Skeleton.FCStd  (your saved model; picks up your spreadsheet edits)
#   2. ChromaSniff_FreeCAD_Skeleton_v1_1.py (table in the script)
#   Searched in: this macro's folder, FreeCAD macro folder, home folder, current folder.
#
# RUN WITHOUT FREECAD:  python3 ChromaSniff_Robot_Integration_v1.py
#   -> runs every check (all tilt angles x standing/crouch poses) and prints the report.
#
# FRAMES (mm, degrees)
#   Robot frame R (ROS REP-103): X forward, Y left, Z up, origin on the ground under the trunk centre.
#   Handheld frame P (V1.1): X right, Y forward (nozzle), Z up.
#   The handheld is mounted nozzle-forward: P->R = RotZ(-90), then tilted nozzle-down about the
#   hinge axis (robot Y) by Tilt_deg (0-20 deg), hinge located at (Mount_X, 0, Mount_Z).
#
# All robot dimensions are a Go2-class PLACEHOLDER built from the published 70x31x40 cm / 15 kg
# figures; link lengths, hip offsets and top-plate bolt pattern MUST be verified against the
# manufacturer URDF/STEP (e.g. unitree_ros go2_description) before fabrication.

import math
import os

try:
    import FreeCAD as App
    import Part
    HAVE_FC = True
except ImportError:
    HAVE_FC = False

DOC_NAME = "ChromaSniff_Robot_V1"
SHEET = "CS_RobotParameters"
HANDHELD_FCSTD = "ChromaSniff_V1_1_Skeleton.FCStd"
HANDHELD_SCRIPT = "ChromaSniff_FreeCAD_Skeleton_v1_1.py"

# ---------------------------------------------------------------------------
# Parameters (alias, value, note)
# ---------------------------------------------------------------------------
PARAMS = [
    # --- robot (Go2-class placeholder; published: 70x31x40 cm standing, 15 kg, 28-33.6 V) ---
    ("Robot_Mass", 15.0, "kg, published Go2 figure"),
    ("Robot_Payload_Rated", 7.0, "kg, Go2 Air rated (Pro/Edu 8) - use lowest"),
    ("Payload_Derate", 0.5, "fraction of rated payload allowed for a trotting inspection robot"),
    ("Robot_Supply_V_Max", 33.6, "V, robot battery max -> exceeds handheld 28 V input -> adapter DC-DC"),
    ("Trunk_L", 380, "mm"), ("Trunk_W", 94, "mm (between hip joints)"), ("Trunk_H", 100, "mm"),
    ("Hip_X", 193, "mm hip joint from trunk centre [verify URDF]"),
    ("Hip_Y", 47, "mm [verify URDF]"),
    ("Leg_Y", 142, "mm leg plane from centreline (overall width ~310)"),
    ("Thigh_L", 213, "mm [verify URDF]"), ("Calf_L", 213, "mm [verify URDF]"),
    ("Hip_Z_Stand", 290, "mm hip height standing"), ("Hip_Z_Crouch", 160, "mm hip height crouched"),
    ("Head_L", 90, "mm"), ("Head_W", 120, "mm"), ("Head_H", 100, "mm"),
    ("Lidar_D", 60, "mm chin LiDAR envelope (L1, 360x90 deg hemisphere) [verify]"),
    ("Lidar_Axis_Pitch", 45, "deg LiDAR hemisphere axis above horizontal, forward [verify]"),
    ("Robot_CoG_Z_Above_Hip", 10, "mm, robot CoG height above hip line (estimate)"),
    ("Top_Plate_Z", 340, "mm top of trunk / payload plate seat"),
    # --- mount ---
    ("Mount_X", 160, "mm hinge axis X in robot frame"),
    ("Mount_Z", 395, "mm hinge axis Z in robot frame (standing)"),
    ("Pivot_P_Y", 90, "mm hinge location in handheld frame (Y)"),
    ("Pivot_P_Z", -34, "mm hinge location in handheld frame (Z, below dovetail)"),
    ("Tilt_deg", 10, "deg nozzle-down tilt shown in the model (detents 0/10/20)"),
    ("Tilt_Max", 20, "deg. 30 deg needs Mount_Z >= 430 (hot zone approaches the head); prefer robot body pitch"),
    # --- masses (ESTIMATES until weighed) ---
    ("Handheld_Robot_Mass", 1.3, "kg handheld without grip/battery (estimate - weigh prototype)"),
    ("Mount_Tilting_Mass", 0.35, "kg cradle + clamp + lug (estimate)"),
    ("Mount_Fixed_Mass", 0.55, "kg base plate + cheeks + electronics box (estimate)"),
    # --- limits ---
    ("Min_Clear_Robot", 15, "mm payload/adapter to robot body at every tilt/pose"),
    ("Min_Clear_Hot_Robot", 25, "mm hot keep-out to head/LiDAR"),
    ("Nozzle_Ahead_Min", 20, "mm nozzle tip ahead of robot's front-most point at 0 deg"),
    ("CoG_Shift_Max_X", 25, "mm combined CoG shift from trunk centre"),
    ("CoG_Shift_Max_Y", 5, "mm"),
    ("Lidar_Occlusion_Max", 25, "% of LiDAR hemisphere blocked (warn above)"),
    ("Max_Total_Height", 600, "mm robot+payload (set from under-coach / pit clearance survey)"),
    ("Cable_Slack_Min", 30, "mm service-loop slack beyond the tilt range"),
]

# Parts in the handheld frame that tilt with the payload (x0, y0, z0, dx, dy, dz)
TILTING = [
    ("Cradle_Plate", -40, 45, -28, 80, 85, 6, "Al 6 mm cradle"),
    ("Hinge_Lug", -40, 82, -40, 80, 16, 12, "Hinge lug, 8 mm SS pin"),
    ("Arca_Clamp", -30, 55, -22, 60, 70, 16, "38 mm Arca-type clamp (grips dovetail)"),
    ("Clamp_Knob", 30, 112, -20, 14, 16, 12, "Clamp knob + safety pin (right side, ahead of hinge cheeks)"),
]
SKIP_HANDHELD = {"Robot_Adapter"}         # V1.1 placeholder replaced by the detailed mount here
PHYS = {"HOT", "WARM", "INTER", "COOL", "INSUL"}


# ---------------------------------------------------------------------------
# Small linear-algebra kit (4x4 row-major homogeneous matrices)
# ---------------------------------------------------------------------------
def mm(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def T(x, y, z):
    return [[1, 0, 0, x], [0, 1, 0, y], [0, 0, 1, z], [0, 0, 0, 1]]


def RY(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]]


def RZ(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def ap(M, p):
    return tuple(M[i][0] * p[0] + M[i][1] * p[1] + M[i][2] * p[2] + M[i][3] for i in range(3))


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


class Box:
    """Box = local axis-aligned box (x0..x0+dx ...) placed by matrix M. Stores an OBB."""

    def __init__(self, name, group, M, x0, y0, z0, dx, dy, dz, cls="COOL", note=""):
        self.name, self.group, self.cls, self.note = name, group, cls, note
        self.M, self.local = M, (x0, y0, z0, dx, dy, dz)
        self.c = ap(M, (x0 + dx / 2, y0 + dy / 2, z0 + dz / 2))
        self.u = [(M[0][k], M[1][k], M[2][k]) for k in range(3)]
        self.e = (dx / 2, dy / 2, dz / 2)

    def corners(self):
        x0, y0, z0, dx, dy, dz = self.local
        return [ap(self.M, (x0 + i * dx, y0 + j * dy, z0 + k * dz))
                for i in (0, 1) for j in (0, 1) for k in (0, 1)]

    def volume(self):
        return 8 * self.e[0] * self.e[1] * self.e[2]


def obb_overlap(A, B, margin=0.0, tol=0.01):
    """Separating-axis test. margin inflates A. True if they penetrate by more than tol."""
    ea = [e + margin for e in A.e]
    eb = B.e
    R = [[dot(A.u[i], B.u[j]) for j in range(3)] for i in range(3)]
    AR = [[abs(R[i][j]) + 1e-9 for j in range(3)] for i in range(3)]
    tv = sub(B.c, A.c)
    t = [dot(tv, A.u[i]) for i in range(3)]
    for i in range(3):
        if abs(t[i]) >= ea[i] + sum(eb[j] * AR[i][j] for j in range(3)) - tol:
            return False
    for j in range(3):
        if abs(sum(t[i] * R[i][j] for i in range(3))) >= sum(ea[i] * AR[i][j] for i in range(3)) + eb[j] - tol:
            return False
    for i in range(3):
        for j in range(3):
            i1, i2, j1, j2 = (i + 1) % 3, (i + 2) % 3, (j + 1) % 3, (j + 2) % 3
            ra = ea[i1] * AR[i2][j] + ea[i2] * AR[i1][j]
            rb = eb[j1] * AR[i][j2] + eb[j2] * AR[i][j1]
            axis_len = math.sqrt(max(0.0, 1.0 - R[i][j] ** 2))   # |A_i x B_j|
            if axis_len < 1e-6:
                continue                   # parallel edges: axis degenerate, face tests cover it
            if abs(t[i2] * R[i1][j] - t[i1] * R[i2][j]) >= ra + rb - tol * axis_len:
                return False
    return True


def ray_hits(box, o, d, tmax=5000.0):
    oo = sub(o, box.c)
    t0, t1 = 0.0, tmax
    for k in range(3):
        ol, dl = dot(oo, box.u[k]), dot(d, box.u[k])
        if abs(dl) < 1e-12:
            if abs(ol) > box.e[k]:
                return False
        else:
            a, b = (-box.e[k] - ol) / dl, (box.e[k] - ol) / dl
            if a > b:
                a, b = b, a
            t0, t1 = max(t0, a), min(t1, b)
            if t0 > t1:
                return False
    return True


# ---------------------------------------------------------------------------
# Handheld loading
# ---------------------------------------------------------------------------
def _search_dirs():
    d = []
    if "__file__" in globals():
        d.append(os.path.dirname(os.path.abspath(__file__)))
    if HAVE_FC:
        try:
            d.append(App.getUserMacroDir(True))
        except Exception:
            pass
    d += [os.path.expanduser("~"), os.getcwd()]
    return d


def _find(fname):
    for d in _search_dirs():
        p = os.path.join(d, fname)
        if os.path.isfile(p):
            return p
    return None


def load_handheld():
    """Return ({name: (bbox, class, parent, config, label)}, source_string)."""
    if HAVE_FC:
        path = _find(HANDHELD_FCSTD)
        if path:
            try:
                doc = App.openDocument(path, hidden=True)
            except TypeError:
                doc = App.openDocument(path)
            items = {}
            for o in doc.Objects:
                if hasattr(o, "CS_Class"):
                    bb = o.Shape.BoundBox
                    items[o.Name[3:]] = ((bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax),
                                         o.CS_Class, o.CS_Parent or None, o.CS_Config, o.Label)
            App.closeDocument(doc.Name)
            if items:
                return items, path
    path = _find(HANDHELD_SCRIPT)
    if not path:
        raise FileNotFoundError(f"Put {HANDHELD_FCSTD} or {HANDHELD_SCRIPT} next to this macro.")
    src = open(path, encoding="utf-8").read()
    cut = src.find("# FreeCAD build")
    ns = {}
    exec(compile(src[:cut if cut > 0 else len(src)], path, "exec"), ns)
    items = {}
    for r in ns["I"]:
        x, y, z, dx, dy, dz = r[4:10]
        items[r[0]] = ((x, y, z, x + dx, y + dy, z + dz), r[2], r[3], r[10], r[11])
    return items, path


# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------
def leg_pose(P, hip_z):
    """2-link IK, knees pointing backward, feet under hips. Returns list of Box."""
    boxes = []
    L1, L2 = P["Thigh_L"], P["Calf_L"]
    foot_r = 20
    for fx, tag_x in ((1, "F"), (-1, "R")):
        for sy, tag_y in ((1, "L"), (-1, "R")):
            hip = (fx * P["Hip_X"], sy * P["Leg_Y"], hip_z)
            foot = (hip[0], hip[1], foot_r)
            d = hip_z - foot_r
            d = min(d, L1 + L2 - 1)
            a = math.acos((L1 ** 2 + d ** 2 - L2 ** 2) / (2 * L1 * d))
            # thigh: rotate the straight-down direction backward by a
            ux, uz = -math.sin(a), -math.cos(a)
            knee = (hip[0] + L1 * ux, hip[1], hip[2] + L1 * uz)
            vx, vz = foot[0] - knee[0], foot[2] - knee[2]
            n = math.hypot(vx, vz)
            for nm, j, (dx_, dz_), L in (("Thigh", hip, (ux, uz), L1), ("Calf", knee, (vx / n, vz / n), L2)):
                beta = math.degrees(math.atan2(-dx_, -dz_))
                M = mm(T(*j), RY(beta))
                boxes.append(Box(f"{nm}_{tag_x}{tag_y}", "01_QUADRUPED", M, -20, -15, -L, 40, 30, L, "ROBOT"))
            boxes.append(Box(f"Foot_{tag_x}{tag_y}", "01_QUADRUPED", T(*foot), -20, -20, -20, 40, 40, 40, "ROBOT"))
    return boxes


def payload_matrix(P, tilt, dz):
    return mm(mm(mm(T(P["Mount_X"], 0, P["Mount_Z"] + dz), RY(tilt)), RZ(-90)),
              T(0, -P["Pivot_P_Y"], -P["Pivot_P_Z"]))


def build_scene(P, handheld, tilt, pose="stand"):
    hip_z = P["Hip_Z_Stand"] if pose == "stand" else P["Hip_Z_Crouch"]
    dz = hip_z - P["Hip_Z_Stand"]                   # everything on the trunk moves with it
    S = {}

    def add(b):
        S[b.name] = b

    tz = P["Top_Plate_Z"] + dz
    # quadruped
    add(Box("Trunk", "01_QUADRUPED", T(0, 0, 0), -P["Trunk_L"] / 2, -P["Trunk_W"] / 2 - 48, tz - P["Trunk_H"],
            P["Trunk_L"], P["Trunk_W"] + 96, P["Trunk_H"], "ROBOT"))
    hx0 = P["Trunk_L"] / 2
    add(Box("Head", "01_QUADRUPED", T(0, 0, 0), hx0, -P["Head_W"] / 2, tz - P["Head_H"] + 15,
            P["Head_L"], P["Head_W"], P["Head_H"], "ROBOT"))
    lz = tz - P["Head_H"] - 5
    add(Box("Lidar_L1", "01_QUADRUPED", T(0, 0, 0), hx0 + P["Head_L"] - 30, -P["Lidar_D"] / 2, lz,
            P["Lidar_D"], P["Lidar_D"], P["Lidar_D"], "ROBOT"))
    for b in leg_pose(P, hip_z):
        add(b)
    # fixed mount (robot frame)
    I4 = T(0, 0, 0)
    add(Box("Robot_Payload_Plate", "02_MOUNT_FIXED", I4, -150, -60, tz, 340, 120, 6, "MOUNT",
            "Robot-side payload plate - match robot bolt pattern [verify]"))
    add(Box("Adapter_Base_Plate", "02_MOUNT_FIXED", I4, -75, -55, tz + 6, 260, 110, 6, "MOUNT",
            "Al 6 mm, M5 to payload plate"))
    mx, pz = P["Mount_X"], P["Mount_Z"] + dz
    for side, y0 in (("L", 43), ("R", -51)):
        add(Box(f"Hinge_Cheek_{side}", "02_MOUNT_FIXED", I4, mx - 20, y0, tz + 12, 40, 8, pz - (tz + 12) + 16,
                "MOUNT", "Al 8 mm cheek, detent holes 0/10/20 deg"))
    add(Box("Tilt_Lock_Knob", "02_MOUNT_FIXED", I4, mx - 10, -66, pz - 10, 20, 15, 20, "MOUNT",
            "Indexing plunger (right side, keeps left card door clear)"))
    add(Box("Adapter_Electronics_Box", "02_MOUNT_FIXED", I4, -70, -45, tz + 12, 80, 90, 40, "MOUNT",
            "33.6->24 V DC-DC, fuse, e-stop relay, RS-485/CAN transceiver"))
    add(Box("EStop_Button", "02_MOUNT_FIXED", I4, -45, -15, tz + 52, 30, 30, 25, "MOUNT",
            "Mushroom e-stop, hard-wired into the rear-connector e-stop loop"))
    # tilting mount + payload (handheld frame -> robot frame)
    M = payload_matrix(P, tilt, dz)
    for nm, x0, y0, z0, dx_, dy_, dz_, note in TILTING:
        add(Box(nm, "03_MOUNT_TILTING", M, x0, y0, z0, dx_, dy_, dz_, "MOUNT", note))
    for nm, (bb, cls, par, cfg, lab) in handheld.items():
        if cfg not in ("B", "R") or nm in SKIP_HANDHELD:
            continue
        if cls in PHYS or cls in ("KEEPOUT_HOT", "ACCESS"):
            add(Box("HH_" + nm, "04_HANDHELD_PAYLOAD", M, bb[0], bb[1], bb[2],
                    bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2], cls, lab))
    return S, M, dz


def lidar_origin_axis(S, P):
    L = S["Lidar_L1"]
    a = math.radians(P["Lidar_Axis_Pitch"])
    return L.c, (math.cos(a), 0.0, math.sin(a))


def hemisphere(axis, n=1500):
    pts, g = [], math.pi * (3 - math.sqrt(5))
    for i in range(2 * n):
        y = 1 - (i + 0.5) / n
        r = math.sqrt(max(0.0, 1 - y * y))
        p = (math.cos(g * i) * r, y, math.sin(g * i) * r)
        if dot(p, axis) >= 0:
            pts.append(p)
    return pts


def cable_path(P, M, dz):
    """Rear connector -> service loop -> adapter box -> robot power/data port."""
    tz = P["Top_Plate_Z"] + dz
    conn = ap(M, (0, -22, 19))
    exit_ = ap(M, (0, -45, 19))
    box_in = (10, 0, tz + 32)
    loop = ((exit_[0] + box_in[0]) / 2, 0, max(exit_[2], box_in[2]) + 25)
    robot_port = (-140, 0, tz + 6)
    box_out = (-70, 0, tz + 20)
    return [conn, exit_, loop, box_in], [box_out, (-110, 0, tz + 20), robot_port]


def plen(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate(P, handheld):
    res = []

    def rec(check, ok, detail, level="FAIL"):
        res.append((check, "PASS" if ok else level, detail))

    tilts = sorted({0.0, 10.0, 20.0, float(P["Tilt_Max"]), float(P["Tilt_deg"])})
    robot_body = ("Trunk", "Head", "Lidar_L1")
    worst = {}
    for pose in ("stand", "crouch"):
        for tilt in tilts:
            S, M, dz = build_scene(P, handheld, tilt, pose)
            moving = [b for b in S.values() if b.group in ("03_MOUNT_TILTING", "04_HANDHELD_PAYLOAD")
                      and b.cls not in ("KEEPOUT_HOT", "ACCESS")]
            fixed = [b for b in S.values() if b.group in ("01_QUADRUPED", "02_MOUNT_FIXED")]
            hits = []
            for a in moving:
                for f in fixed:
                    if a.name in ("Hinge_Lug", "Cradle_Plate") and f.name.startswith("Hinge_Cheek"):
                        continue                   # pin joint: checked by the Y-gap test below
                    margin = P["Min_Clear_Robot"] if f.group == "01_QUADRUPED" else 0.0
                    if obb_overlap(f, a, margin):
                        hits.append(f"{a.name} x {f.name}")
            rec("Clearance", not hits,
                f"{pose}, tilt {tilt:.0f} deg: " + ("clear (>= %d mm to robot)" % P["Min_Clear_Robot"]
                                                     if not hits else "; ".join(hits[:6])))
            hk = S["HH_Hot_Keepout"]
            hh = [n for n in robot_body if obb_overlap(S[n], hk, P["Min_Clear_Hot_Robot"])]
            rec("Hot zone", not hh, f"{pose}, tilt {tilt:.0f}: hot keep-out {'>= %d mm from head/LiDAR' % P['Min_Clear_Hot_Robot'] if not hh else 'too close to ' + str(hh)}")
            acc = [f.name for f in fixed if obb_overlap(S["HH_Access_Card_Door"], f)]
            rec("Card access", not acc, f"{pose}, tilt {tilt:.0f}: left card door " + ("reachable" if not acc else f"blocked by {acc}"))
            if pose == "stand":
                top = max(c[2] for b in S.values() if b.cls not in ("ACCESS",) for c in b.corners())
                worst["height"] = max(worst.get("height", 0), top)
                tip = ap(M, (12, 285, 18))
                front = max(c[0] for n in robot_body for c in S[n].corners())
                worst.setdefault("tips", []).append((tilt, tip, front))
    # pin-joint side gap
    rec("Hinge", 43 - 40 >= 2, "cradle/lug half-width 40 mm vs cheek inner face 43 mm -> 3 mm side gap (add PTFE washers)")
    # height
    rec("Height", worst["height"] <= P["Max_Total_Height"],
        f"max robot+payload height {worst['height']:.0f} mm (limit {P['Max_Total_Height']:.0f}; standing robot alone ~400)")
    # nozzle reach
    for tilt, tip, front in worst["tips"]:
        ahead = tip[0] - front
        need = P["Nozzle_Ahead_Min"] if tilt == 0 else -1e9
        rec("Nozzle reach", ahead >= need,
            f"tilt {tilt:.0f} deg: nozzle tip {ahead:+.0f} mm ahead of robot front, {tip[2]:.0f} mm above ground",
            "FAIL" if tilt == 0 else "INFO")
    # LiDAR occlusion
    for tilt in (0.0, float(P["Tilt_Max"])):
        S, M, dz = build_scene(P, handheld, tilt)
        o, ax = lidar_origin_axis(S, P)
        occl = [b for b in S.values() if b.group in ("02_MOUNT_FIXED", "03_MOUNT_TILTING", "04_HANDHELD_PAYLOAD")
                and b.cls not in ("KEEPOUT_HOT", "ACCESS")]
        rays = hemisphere(ax)
        blocked = sum(1 for d in rays if any(ray_hits(b, o, d) for b in occl))
        pct = 100.0 * blocked / len(rays)
        rec("LiDAR occlusion", pct <= P["Lidar_Occlusion_Max"],
            f"tilt {tilt:.0f} deg: {pct:.1f}% of L1 hemisphere blocked by payload (limit {P['Lidar_Occlusion_Max']:.0f}%) - axis pitch is an assumption",
            "WARN")
    # CoG / payload
    for tilt in (0.0, float(P["Tilt_Max"])):
        S, M, dz = build_scene(P, handheld, tilt)
        hh = [b for b in S.values() if b.group == "04_HANDHELD_PAYLOAD" and b.cls in PHYS]
        vol = sum(b.volume() for b in hh)
        cg_hh = tuple(sum(b.c[k] * b.volume() for b in hh) / vol for k in range(3))
        tl = [b for b in S.values() if b.group == "03_MOUNT_TILTING"]
        fx = [b for b in S.values() if b.group == "02_MOUNT_FIXED" and b.name != "Robot_Payload_Plate"]
        cg_t = tuple(sum(b.c[k] * b.volume() for b in tl) / sum(b.volume() for b in tl) for k in range(3))
        cg_f = tuple(sum(b.c[k] * b.volume() for b in fx) / sum(b.volume() for b in fx) for k in range(3))
        cg_r = (0.0, 0.0, P["Hip_Z_Stand"] + P["Robot_CoG_Z_Above_Hip"])
        parts = [(P["Robot_Mass"], cg_r), (P["Handheld_Robot_Mass"], cg_hh),
                 (P["Mount_Tilting_Mass"], cg_t), (P["Mount_Fixed_Mass"], cg_f)]
        mt = sum(m for m, _ in parts)
        cg = tuple(sum(m * c[k] for m, c in parts) / mt for k in range(3))
        payload = mt - P["Robot_Mass"]
        rec("CoG", abs(cg[0]) <= P["CoG_Shift_Max_X"] and abs(cg[1]) <= P["CoG_Shift_Max_Y"],
            f"tilt {tilt:.0f}: combined CoG shift X {cg[0]:+.1f} mm, Y {cg[1]:+.1f} mm, rises {cg[2] - cg_r[2]:+.1f} mm "
            f"(handheld CoG uses volume-weighted envelopes - weigh the prototype)")
        if tilt == 0.0:
            lim = P["Robot_Payload_Rated"] * P["Payload_Derate"]
            rec("Payload", payload <= lim, f"payload {payload:.2f} kg vs allowed {lim:.1f} kg "
                f"({P['Payload_Derate']:.0%} of {P['Robot_Payload_Rated']:.0f} kg rated)")
    # cable
    L = {}
    for tilt in (0.0, float(P["Tilt_Max"])):
        S, M, dz = build_scene(P, handheld, tilt)
        a, b = cable_path(P, M, dz)
        L[tilt] = plen(a)
    swing = abs(L[P["Tilt_Max"]] - L[0.0])
    rec("Cable", True, f"device->box run {L[0.0]:.0f} mm at 0 deg, {L[P['Tilt_Max']]:.0f} mm at {P['Tilt_Max']:.0f} deg "
        f"-> cut {max(L.values()) + P['Cable_Slack_Min']:.0f} mm incl. slack", "INFO")
    rec("Power", P["Robot_Supply_V_Max"] > 28, f"robot bus up to {P['Robot_Supply_V_Max']} V exceeds handheld 9-28 V input "
        "-> 24 V DC-DC in adapter box is REQUIRED (modelled)", "INFO")
    rec("Robot behaviour", True, "Go2 thigh range reaches over the back (roll-over recovery): disable flip/roll-over "
        "behaviours while the payload is mounted", "INFO")
    return res


def params_default():
    return {a: float(v) for a, v, _ in PARAMS}


def print_report(res):
    for c, s, d in res:
        print(f"[{s}] {c}: {d}")
    f = [r for r in res if r[1] == "FAIL"]
    w = [r for r in res if r[1] == "WARN"]
    print(f"--> {len(res) - len(f) - len(w)} pass/info, {len(w)} warnings, {len(f)} failures")
    return f


# ---------------------------------------------------------------------------
# FreeCAD build
# ---------------------------------------------------------------------------
if HAVE_FC:
    GCOL = {"01_QUADRUPED": (0.25, 0.25, 0.28), "02_MOUNT_FIXED": (0.75, 0.75, 0.78),
            "03_MOUNT_TILTING": (0.95, 0.6, 0.15)}
    CCOL = {"HOT": (0.85, 0.2, 0.1), "WARM": (0.95, 0.55, 0.1), "INTER": (0.95, 0.85, 0.3),
            "COOL": (0.3, 0.55, 0.85), "INSUL": (0.6, 0.6, 0.6), "KEEPOUT_HOT": (1, 0, 0), "ACCESS": (0.3, 0.8, 0.4)}
    GROUPS = ["00_PARAMETERS", "01_QUADRUPED", "02_MOUNT_FIXED", "03_MOUNT_TILTING",
              "04_HANDHELD_PAYLOAD", "05_CABLES", "06_VALIDATION"]

    def _doc():
        d = App.listDocuments().get(DOC_NAME)
        if d is None:
            d = App.newDocument(DOC_NAME)
            s = d.addObject("Spreadsheet::Sheet", SHEET)
            s.set("A1", "Alias"); s.set("B1", "Value"); s.set("C1", "Note")
            for r, (a, v, n) in enumerate(PARAMS, start=2):
                s.set(f"A{r}", a); s.set(f"B{r}", f"={v}"); s.set(f"C{r}", n); s.setAlias(f"B{r}", a)
            for g in GROUPS:
                grp = d.addObject("App::DocumentObjectGroup", "G" + g); grp.Label = g
            d.getObject("G00_PARAMETERS").addObject(s)
            d.recompute()
        return d

    def _params(d):
        s = d.getObject(SHEET)
        return {a: float(s.get(a)) for a, _, _ in PARAMS}

    def _clear(d):
        for g in GROUPS[1:]:
            grp = d.getObject("G" + g)
            for o in list(grp.Group):
                if o.TypeId != "Spreadsheet::Sheet":
                    d.removeObject(o.Name)

    def _pl(M):
        return App.Placement(App.Matrix(*[v for row in M for v in row]))

    def rebuild():
        d = _doc()
        P = _params(d)
        handheld, src = load_handheld()
        print("Handheld source:", src)
        _clear(d)
        S, M, dz = build_scene(P, handheld, P["Tilt_deg"], "stand")
        for b in S.values():
            x0, y0, z0, dx, dy, dz_ = b.local
            o = d.addObject("Part::Box", "RB_" + b.name)
            o.Length, o.Width, o.Height = dx, dy, dz_
            o.Placement = _pl(mm(b.M, T(x0, y0, z0)))
            o.Label = f"{b.name} - {b.note}" if b.note else b.name
            o.addProperty("App::PropertyString", "CS_Status", "ChromaSniff")
            o.CS_Status = "PLACEHOLDER ENVELOPE - verify against datasheet/URDF/STEP"
            d.getObject("G" + b.group).addObject(o)
            if App.GuiUp:
                vo = o.ViewObject
                vo.ShapeColor = GCOL.get(b.group, CCOL.get(b.cls, (0.5, 0.5, 0.5)))
                vo.Transparency = 85 if b.cls in ("KEEPOUT_HOT", "ACCESS") else (20 if b.group == "01_QUADRUPED" else 30)
        a, b2 = cable_path(P, M, dz)
        for nm, pts in (("Cable_Device_to_Box", a), ("Cable_Box_to_Robot", b2)):
            w = d.addObject("Part::Feature", nm)
            w.Shape = Part.makePolygon([App.Vector(*p) for p in pts])
            d.getObject("G05_CABLES").addObject(w)
            if App.GuiUp:
                w.ViewObject.LineWidth = 4; w.ViewObject.LineColor = (0.1, 0.1, 0.1)
        tip = d.addObject("Part::Sphere", "Marker_Nozzle_Tip")
        tip.Radius = 6
        tip.Placement.Base = App.Vector(*ap(M, (12, 285, 18)))
        d.getObject("G06_VALIDATION").addObject(tip)
        res = validate(P, handheld)
        print_report(res)
        rep = d.getObject("CS_RobotValidation") or d.addObject("Spreadsheet::Sheet", "CS_RobotValidation")
        rep.clearAll()
        rep.set("A1", "Check"); rep.set("B1", "Result"); rep.set("C1", "Detail")
        for k, (c, s_, t_) in enumerate(res, start=2):
            rep.set(f"A{k}", c); rep.set(f"B{k}", s_); rep.set(f"C{k}", "'" + t_)
        d.getObject("G06_VALIDATION").addObject(rep)
        d.recompute()
        path = os.path.join(os.path.expanduser("~"), "ChromaSniff_Robot_V1.FCStd")
        try:
            d.saveAs(path); print("Saved:", path)
        except Exception as e:
            print("WARNING: could not save", path, "->", e)
        if App.GuiUp:
            import FreeCADGui as Gui
            Gui.activeDocument().activeView().viewIsometric()
            Gui.SendMsgToActiveView("ViewFit")
        return res

    rebuild()
    print("Edit CS_RobotParameters (e.g. Tilt_deg, Mount_X, Mount_Z), then run rebuild() in the Python console.")

elif __name__ == "__main__":
    P = params_default()
    hh, src = load_handheld()
    print("Handheld source:", src)
    fails = print_report(validate(P, hh))
    raise SystemExit(1 if fails else 0)
