#!/usr/bin/env python3
"""Remap a Keychron Q60 (wired, QMK/VIA) to the HHKB Professional layout.

Talks the VIA raw-HID protocol directly over /dev/hidrawN, so changes are
stored in the keyboard's EEPROM (same as using usevia.app).

  python3 hhkb_q60.py backup            # dump current keymap to JSON
  python3 hhkb_q60.py apply             # backup, then write HHKB layout
  python3 hhkb_q60.py restore FILE.json # write a backup back
"""
import glob, json, os, sys, time

VID, PID = 0x3434, 0x01C0
ROWS, COLS = 5, 14

# --- QMK basic keycodes -----------------------------------------------------
TRNS, NO = 0x01, 0x00
BSPC, CAPS = 0x2A, 0x39
F = {i: 0x3A + i - 1 for i in range(1, 13)}  # F1..F12
PSCR, SCRL, PAUS, INS, HOME, PGUP, DEL, END, PGDN = range(0x46, 0x4F)
RGHT, LEFT, DOWN, UP = 0x4F, 0x50, 0x51, 0x52
PSLS, PAST, PMNS, PPLS, PENT = 0x54, 0x55, 0x56, 0x57, 0x58
PWR = 0x66
MUTE, VOLU, VOLD, EJCT = 0xA8, 0xA9, 0xAA, 0xB0

# Matrix positions (row, col) on the Q60
POS = {
    "esc": (0, 0), **{str(n % 10): (0, n) for n in range(1, 11)},
    "-": (0, 11), "=": (0, 12), "\\": (0, 13), "`": (4, 12),
    "tab": (1, 0), "q": (1, 1), "i": (1, 8), "o": (1, 9), "p": (1, 10),
    "[": (1, 11), "]": (1, 12), "bs": (1, 13),
    "ctrl": (2, 0), "a": (2, 1), "s": (2, 2), "d": (2, 3), "f": (2, 4),
    "h": (2, 6), "j": (2, 7), "k": (2, 8), "l": (2, 9), ";": (2, 10),
    "'": (2, 11), "enter": (2, 13),
    "lshift": (3, 0), "n": (3, 7), "m": (3, 8), ",": (3, 9), ".": (3, 10),
    "/": (3, 11), "rshift": (3, 12), "fn": (3, 13),
}

# HHKB Professional 2 / Hybrid Fn layer
HHKB_FN = {
    "esc": PWR, "1": F[1], "2": F[2], "3": F[3], "4": F[4], "5": F[5],
    "6": F[6], "7": F[7], "8": F[8], "9": F[9], "0": F[10], "-": F[11],
    "=": F[12], "\\": INS, "`": DEL,
    "tab": CAPS, "i": PSCR, "o": SCRL, "p": PAUS, "[": UP, "bs": DEL,
    "a": VOLD, "s": VOLU, "d": MUTE, "f": EJCT,
    "h": PAST, "j": PSLS, "k": HOME, "l": PGUP, ";": LEFT, "'": RGHT,
    "enter": PENT,
    "n": PPLS, "m": PMNS, ",": END, ".": PGDN, "/": DOWN,
}

MAC_BASE, WIN_BASE, FN_LAYER, EXTRA_LAYER = 0, 1, 2, 3


# --- VIA transport ----------------------------------------------------------
def find_dev():
    for h in sorted(glob.glob("/sys/class/hidraw/hidraw*")):
        dev = os.path.realpath(os.path.join(h, "device"))
        name = os.path.basename(dev)  # e.g. 0003:3434:01C0.0018
        if f"{VID:04X}:{PID:04X}" not in name.upper():
            continue
        with open(os.path.join(dev, "report_descriptor"), "rb") as f:
            if f.read(3) == b"\x06\x60\xff":  # usage page 0xFF60 = VIA
                return "/dev/" + os.path.basename(h)
    sys.exit("Q60 VIA interface not found")


class Via:
    def __init__(self, path):
        try:
            self.fd = os.open(path, os.O_RDWR)
        except PermissionError:
            sys.exit(f"No permission on {path}. Run:  sudo chmod a+rw {path}")

    def cmd(self, *data):
        pkt = bytes(data) + bytes(32 - len(data))
        os.write(self.fd, b"\x00" + pkt)
        resp = os.read(self.fd, 32)
        if resp[0] == 0xFF:
            raise RuntimeError(f"VIA command 0x{data[0]:02x} unhandled")
        return resp

    def protocol(self):
        r = self.cmd(0x01)
        return r[1] << 8 | r[2]

    def layers(self):
        return self.cmd(0x11)[1]

    def get(self, layer, row, col):
        r = self.cmd(0x04, layer, row, col)
        return r[4] << 8 | r[5]

    def set(self, layer, row, col, kc):
        self.cmd(0x05, layer, row, col, kc >> 8, kc & 0xFF)

    def dump(self):
        return [[[self.get(l, r, c) for c in range(COLS)] for r in range(ROWS)]
                for l in range(self.layers())]


def backup(via):
    km = via.dump()
    path = f"q60_backup_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(path, "w") as f:
        json.dump({"protocol": via.protocol(), "keymap": km}, f)
    print(f"Backup saved: {path}")
    return km


def write_layer(via, layer, grid, current):
    for r in range(ROWS):
        for c in range(COLS):
            if grid[r][c] != current[layer][r][c]:
                via.set(layer, r, c, grid[r][c])


def apply(via):
    km = backup(via)
    if len(km) < 4:
        sys.exit(f"Expected >=4 layers, got {len(km)}")
    fn_r, fn_c = POS["fn"]
    mo_fn = km[MAC_BASE][fn_r][fn_c]          # existing MO(2), encoding varies
    mo_extra = mo_fn - FN_LAYER + EXTRA_LAYER  # MO(3) in the same encoding

    # Base layers: key above Enter is Backspace on HHKB (Keychron ships Delete)
    new = [[row[:] for row in layer] for layer in km]
    for base in (MAC_BASE, WIN_BASE):
        r, c = POS["bs"]
        new[base][r][c] = BSPC

    # Move Keychron's original Fn layer (RGB controls, NKRO toggle) to layer 3
    new[EXTRA_LAYER] = [row[:] for row in km[FN_LAYER]]
    r, c = POS["fn"]
    new[EXTRA_LAYER][r][c] = TRNS

    # Layer 2 = pure HHKB Fn layer; Fn+RShift (unused on HHKB) opens layer 3
    fn = [[TRNS] * COLS for _ in range(ROWS)]
    for key, kc in HHKB_FN.items():
        r, c = POS[key]
        fn[r][c] = kc
    r, c = POS["rshift"]
    fn[r][c] = mo_extra
    new[FN_LAYER] = fn

    for layer in (MAC_BASE, WIN_BASE, FN_LAYER, EXTRA_LAYER):
        write_layer(via, layer, new[layer], km)

    if via.dump()[:4] != new[:4]:
        sys.exit("Verification FAILED - keymap readback differs")
    print("HHKB layout written and verified.")


def restore(via, path):
    with open(path) as f:
        km = json.load(f)["keymap"]
    cur = via.dump()
    for layer in range(min(len(km), len(cur))):
        write_layer(via, layer, km[layer], cur)
    print("Restored", path)


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "backup"
    via = Via(find_dev())
    print(f"VIA protocol 0x{via.protocol():04x}, {via.layers()} layers")
    if action == "backup":
        backup(via)
    elif action == "apply":
        apply(via)
    elif action == "restore":
        restore(via, sys.argv[2])
    else:
        sys.exit(__doc__)
