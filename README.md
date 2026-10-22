<p align="center">
  <img src="assets/wordmark.svg" alt="Q60 HHKB" width="560">
</p>

<p align="center">
  Happy Hacking layout on a Keychron Q60 (wired, QMK / VIA)<br>
  <a href="https://shrac1234.github.io/Q60_HHKB/q60-hhkb-guide.html">Interactive guide</a>
</p>

---

`hhkb_q60.py` remaps a regular wired **Keychron Q60** (USB `3434:01C0`) to the **HHKB Professional** layout. It writes the keymap over the VIA raw-HID protocol, the same way usevia.app does. That means:

- no firmware flashing
- the layout is stored on the keyboard and works on any computer
- you can still open and edit the result in VIA

Python 3 on Linux. No extra packages.

## What changes

The Q60 is already physically an HHKB layout. The script changes three things:

1. **Backspace.** The key above Enter types **Backspace**. Keychron ships it as Delete. **Fn + that key** types **Delete**.
2. **Fn layer.** Fn now works like an HHKB Pro 2: arrows, Home/End, PgUp/PgDn, volume, PrtSc and numpad keys.
3. **Lighting.** Keychron's RGB lighting and NKRO controls move to **Fn + Right Shift**. A real HHKB has no backlight, so this pair is otherwise unused.

### Hold Fn

<img src="assets/fn-layer.svg" alt="Fn layer: Esc=Power, 1-= = F1-F12, \=Ins, `=Del, Tab=Caps, I/O/P=PrtSc/ScrLk/Pause, [=Up, BS=Del, A/S/D/F=Vol-/Vol+/Mute/Eject, H/J=*,/, K/L=Home/PgUp, ;/'=Left/Right, Enter=Numpad Enter, N/M=+/-, ,/.=End/PgDn, /=Down" width="100%">

| Group | Keys |
|---|---|
| Arrows and paging | <kbd>Fn</kbd> + <kbd>[</kbd> ↑ · <kbd>/</kbd> ↓ · <kbd>;</kbd> ← · <kbd>'</kbd> → · <kbd>K</kbd> Home · <kbd>,</kbd> End · <kbd>L</kbd> PgUp · <kbd>.</kbd> PgDn |
| Editing | <kbd>BS</kbd> Backspace · <kbd>Fn</kbd> + <kbd>BS</kbd> Delete · <kbd>Fn</kbd> + <kbd>`</kbd> Delete · <kbd>Fn</kbd> + <kbd>\\</kbd> Insert · <kbd>Fn</kbd> + <kbd>Tab</kbd> Caps Lock |
| Function row | <kbd>Fn</kbd> + <kbd>1</kbd>…<kbd>0</kbd> F1–F10 · <kbd>-</kbd> F11 · <kbd>=</kbd> F12 |
| Media | <kbd>Fn</kbd> + <kbd>A</kbd> Vol − · <kbd>S</kbd> Vol + · <kbd>D</kbd> Mute · <kbd>F</kbd> Eject (macOS) |
| Numpad | <kbd>Fn</kbd> + <kbd>H</kbd> * · <kbd>J</kbd> / · <kbd>N</kbd> + · <kbd>M</kbd> − · <kbd>Enter</kbd> Numpad Enter |
| System | <kbd>Fn</kbd> + <kbd>I</kbd> PrtSc · <kbd>O</kbd> ScrLk · <kbd>P</kbd> Pause · <kbd>Esc</kbd> Power |

### Hold Fn + Right Shift

<img src="assets/lighting-layer.svg" alt="Lighting layer: Tab=RGB on/off, Q/A=next/previous effect, W/S=brighter/dimmer, E/D=hue, R/F=saturation, T/G=effect speed, N=NKRO toggle" width="100%">

| Key | Up | Key | Down |
|---|---|---|---|
| <kbd>Tab</kbd> | Backlight on / off | | |
| <kbd>Q</kbd> | Next effect | <kbd>A</kbd> | Previous effect |
| <kbd>W</kbd> | Brighter | <kbd>S</kbd> | Dimmer |
| <kbd>E</kbd> | Hue forward | <kbd>D</kbd> | Hue back |
| <kbd>R</kbd> | More saturation | <kbd>F</kbd> | Less saturation |
| <kbd>T</kbd> | Faster effect | <kbd>G</kbd> | Slower effect |
| <kbd>N</kbd> | NKRO on / off | | |

### Mac / Windows switch

The slide switch on the side picks the base layer. Only the bottom row differs.

| Position | Bottom row |
|---|---|
| Mac (layer 0) | <kbd>Option</kbd> <kbd>Cmd</kbd> <kbd>Space</kbd> <kbd>Cmd</kbd> <kbd>Option</kbd> |
| Windows (layer 1) | <kbd>Win</kbd> <kbd>Alt</kbd> <kbd>Space</kbd> <kbd>Alt</kbd> <kbd>Win</kbd> |

## Usage

**1. Allow access to the keyboard.** On Linux, only root can write to the keyboard's VIA interface by default. To allow it until you unplug the keyboard (the hidraw number can vary; the script prints the right one if access fails):

```sh
sudo chmod a+rw /dev/hidraw9
```

To allow it permanently, which also lets usevia.app connect in Chrome:

```sh
echo 'KERNEL=="hidraw*", ATTRS{idVendor}=="3434", ATTRS{idProduct}=="01c0", MODE="0660", TAG+="uaccess"' \
  | sudo tee /etc/udev/rules.d/99-keychron-q60.rules
sudo udevadm control --reload && sudo udevadm trigger
```

**2. Run the script.**

```sh
python3 hhkb_q60.py backup             # save every layer to q60_backup_<timestamp>.json
python3 hhkb_q60.py apply              # back up, write the HHKB layout, read it back to verify
python3 hhkb_q60.py restore FILE.json  # write a backup back to the keyboard
```

`apply` always saves a backup first. To undo the change, restore the backup it made.

**3. Fine-tune in VIA (optional).** Open usevia.app in Chrome or Chromium and authorize the Q60. VIA's layers line up with this layout:

| VIA layer | Use |
|---|---|
| 0 | Mac |
| 1 | Windows |
| 2 | Fn |
| 3 | Fn + Right Shift |
| 4, 5 | Empty, free for your own keys |

## Files

| File | What it is |
|---|---|
| `hhkb_q60.py` | The remapping script |
| `q60-hhkb-guide.html` | Interactive version of this guide, also served on GitHub Pages |
| `assets/` | Images used in this README |
