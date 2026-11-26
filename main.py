#!/usr/bin/env python3
"""THE WORLD TODAY - front-page image of Thursday 26 November 2026.

Draws a one-page newspaper (1024x1024) entirely at run time with the
standard library only: own PNG encoder (zlib + struct), own canvas
primitives and own 5x7 bitmap font. Deterministic: no randomness, no
time, no network. Writes entry.png to MAKEFUN_OUTPUT_DIR or /output.
"""
import math
import os
import struct
import zlib

W, H = 1024, 1024
PAPER = (251, 248, 240)
INK = (17, 17, 17)
RED = (198, 30, 26)
GREY = (118, 116, 110)
FAINT = (226, 221, 210)
DARKGREY = (70, 69, 64)

# ---------------------------------------------------------------- PNG ----
def png_bytes(rgb, w, h):
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(kind, data):
        c = struct.pack(">I", len(data)) + kind + data
        return c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))

# ------------------------------------------------------------- canvas ----
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.buf = bytearray(bg) * (w * h)

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(c)

    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.buf[i:(x1 - x0) * 3 + i] = bytes(c) * (x1 - x0)

    def frame(self, x, y, w, h, c, t=2):
        self.rect(x, y, w, t, c)
        self.rect(x, y + h - t, w, t, c)
        self.rect(x, y, t, h, c)
        self.rect(x + w - t, y, t, h, c)

    def hline(self, x, y, w, c, t=1):
        self.rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.rect(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.rect(x0 - t // 2, y0 - t // 2, t, t, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, fill=True):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                d = (x - cx) ** 2 + (y - cy) ** 2
                if fill:
                    if d <= r * r:
                        self.px(x, y, c)
                else:
                    if r * r - 2 * r <= d <= r * r:
                        self.px(x, y, c)

    def triangle(self, x0, y0, x1, y1, x2, y2, c):
        minx, maxx = min(x0, x1, x2), max(x0, x1, x2)
        miny, maxy = min(y0, y1, y2), max(y0, y1, y2)
        d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if d == 0:
            return
        for y in range(miny, maxy + 1):
            for x in range(minx, maxx + 1):
                a = ((y1 - y2) * (x - x2) + (x2 - x1) * (y - y2)) / d
                b = ((y2 - y0) * (x - x2) + (x0 - x2) * (y - y2)) / d
                cc = 1 - a - b
                if a >= 0 and b >= 0 and cc >= 0:
                    self.px(x, y, c)

# --------------------------------------------------------------- font ----
# 5x7 bitmap font, uppercase + digits + punctuation. Rows are 5 chars.
FONT = {
"A": ("01110","10001","10001","11111","10001","10001","10001"),
"B": ("11110","10001","10001","11110","10001","10001","11110"),
"C": ("01110","10001","10000","10000","10000","10001","01110"),
"D": ("11110","10001","10001","10001","10001","10001","11110"),
"E": ("11111","10000","10000","11110","10000","10000","11111"),
"F": ("11111","10000","10000","11110","10000","10000","10000"),
"G": ("01110","10001","10000","10111","10001","10001","01111"),
"H": ("10001","10001","10001","11111","10001","10001","10001"),
"I": ("01110","00100","00100","00100","00100","00100","01110"),
"J": ("00111","00010","00010","00010","00010","10010","01100"),
"K": ("10001","10010","10100","11000","10100","10010","10001"),
"L": ("10000","10000","10000","10000","10000","10000","11111"),
"M": ("10001","11011","10101","10101","10001","10001","10001"),
"N": ("10001","11001","10101","10011","10001","10001","10001"),
"O": ("01110","10001","10001","10001","10001","10001","01110"),
"P": ("11110","10001","10001","11110","10000","10000","10000"),
"Q": ("01110","10001","10001","10001","10101","10010","01101"),
"R": ("11110","10001","10001","11110","10100","10010","10001"),
"S": ("01111","10000","10000","01110","00001","00001","11110"),
"T": ("11111","00100","00100","00100","00100","00100","00100"),
"U": ("10001","10001","10001","10001","10001","10001","01110"),
"V": ("10001","10001","10001","10001","10001","01010","00100"),
"W": ("10001","10001","10001","10101","10101","11011","10001"),
"X": ("10001","10001","01010","00100","01010","10001","10001"),
"Y": ("10001","10001","01010","00100","00100","00100","00100"),
"Z": ("11111","00001","00010","00100","01000","10000","11111"),
"0": ("01110","10001","10011","10101","11001","10001","01110"),
"1": ("00100","01100","00100","00100","00100","00100","01110"),
"2": ("01110","10001","00001","00110","01000","10000","11111"),
"3": ("11110","00001","00001","01110","00001","00001","11110"),
"4": ("00010","00110","01010","10010","11111","00010","00010"),
"5": ("11111","10000","11110","00001","00001","10001","01110"),
"6": ("01110","10000","10000","11110","10001","10001","01110"),
"7": ("11111","00001","00010","00100","01000","01000","01000"),
"8": ("01110","10001","10001","01110","10001","10001","01110"),
"9": ("01110","10001","10001","01111","00001","00001","01110"),
" ": ("00000","00000","00000","00000","00000","00000","00000"),
".": ("00000","00000","00000","00000","00000","01100","01100"),
",": ("00000","00000","00000","00000","01100","00100","01000"),
":": ("00000","01100","01100","00000","01100","01100","00000"),
";": ("00000","01100","01100","00000","01100","00100","01000"),
"'": ("00100","00100","01000","00000","00000","00000","00000"),
"-": ("00000","00000","00000","01110","00000","00000","00000"),
"!": ("00100","00100","00100","00100","00100","00000","00100"),
"?": ("01110","10001","00001","00110","00100","00000","00100"),
"%": ("11001","11010","00010","00100","01000","01011","10011"),
"/": ("00001","00010","00010","00100","01000","01000","10000"),
"(": ("00010","00100","01000","01000","01000","00100","00010"),
")": ("01000","00100","00010","00010","00010","00100","01000"),
"&": ("01100","10010","10100","01000","10101","10010","01101"),
"+": ("00000","00100","00100","11111","00100","00100","00000"),
"=": ("00000","00000","11111","00000","11111","00000","00000"),
'"': ("01010","01010","00000","00000","00000","00000","00000"),
"*": ("00000","10101","01110","11111","01110","10101","00000"),
"#": ("01010","01010","11111","01010","11111","01010","01010"),
"$": ("00100","01111","10100","01110","00101","11110","00100"),
}

def text_w(s, scale):
    return len(s) * 6 * scale - scale

def draw_text(cv, x, y, s, color, scale=1, align="left"):
    s = s.upper()
    w = text_w(s, scale)
    if align == "center":
        x = x - w // 2
    elif align == "right":
        x = x - w
    cx = x
    for ch in s:
        glyph = FONT.get(ch, FONT[" "])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "1":
                    cv.rect(cx + col * scale, y + row * scale, scale, scale, color)
        cx += 6 * scale
    return w

def wrap_text(cv, x, y, max_w, s, color, scale=1, lh=None, align="left"):
    """Greedy wrap; returns y after last line."""
    if lh is None:
        lh = 9 * scale
    words = s.split(" ")
    lines, cur = [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    for ln in lines:
        draw_text(cv, x, y, ln, color, scale, align)
        y += lh
    return y

# ------------------------------------------------------------ scenes -----
# Small-story scenes are drawn in a 92px-tall panel; all geometry is
# relative to that panel so nothing is clipped. The lead scene has its
# own taller panel (326px).

def scene_taipei(cv, x, y, w, h):
    """Lead illustration: Taipei 101 tower, cargo ship, tariff chart."""
    cv.rect(x, y, w, h, (233, 228, 216))
    cv.rect(x, y, w, h // 3, (250, 246, 236))
    cv.circle(x + w - 70, y + 52, 30, RED)
    # Taipei 101 silhouette (stepped tower)
    tx = x + 40
    base = y + h - 40
    cv.rect(tx, base - 150, 66, 150, INK)
    for i in range(5):
        ww = 66 - i * 8
        cv.rect(tx + i * 4, base - 150 - (i + 1) * 14, ww, 14, INK)
    cv.rect(tx + 28, base - 150 - 84, 10, 22, INK)
    for r in range(6):
        for c in range(3):
            cv.rect(tx + 8 + c * 18, base - 140 + r * 22, 8, 10, PAPER)
    # second tower
    cv.rect(tx + 100, base - 95, 44, 95, DARKGREY)
    for r in range(4):
        cv.rect(tx + 108, base - 85 + r * 20, 8, 9, PAPER)
        cv.rect(tx + 126, base - 85 + r * 20, 8, 9, PAPER)
    # cargo ship (narrower, clear of the chart)
    sx, sy = x + 170, y + h - 78
    cv.rect(sx, sy, 150, 24, INK)
    cv.triangle(sx + 150, sy, sx + 176, sy + 12, sx + 150, sy + 24, INK)
    for i, col in enumerate((RED, PAPER, RED)):
        cv.rect(sx + 10 + i * 46, sy - 24, 40, 24, col)
        cv.frame(sx + 10 + i * 46, sy - 24, 40, 24, INK, 2)
    cv.rect(sx + 70, sy - 40, 6, 16, INK)
    # waves
    for i in range(5):
        cv.line(x + 170 + i * 40, y + h - 12, x + 192 + i * 40, y + h - 12, INK, 3)
    # tariff chart: rising bars with trend line and 15% tag
    bx = x + w - 150
    by = y + h - 36
    for i, bh in enumerate((22, 36, 54, 78)):
        cv.rect(bx + i * 32, by - bh, 22, bh, RED if i == 3 else INK)
    cv.line(bx - 6, by - 86, bx + 124, by - 92, RED, 4)
    draw_text(cv, bx + 2, by - 120, "15%", RED, 3)

def scene_pushback(cv, x, y, w, h):
    """China wall + EU star circle: two powers answer back."""
    cv.rect(x, y, w, h, (233, 228, 216))
    # Great Wall silhouette, low in the panel
    cv.rect(x + 8, y + h - 26, w - 16, 10, INK)
    for i in range(3):
        cv.rect(x + 14 + i * 40, y + h - 44, 22, 18, INK)
        cv.rect(x + 19 + i * 40, y + h - 54, 12, 10, INK)
    # EU circle of stars, top right
    cx, cy = x + w - 48, y + 38
    cv.circle(cx, cy, 30, (30, 48, 110))
    for i in range(12):
        a = math.pi * 2 * i / 12 - math.pi / 2
        sx = int(cx + 21 * math.cos(a))
        sy = int(cy + 21 * math.sin(a))
        cv.rect(sx - 2, sy - 2, 5, 5, (250, 210, 60))
    # speech bubble with NO, top left
    cv.rect(x + 12, y + 10, 84, 34, PAPER)
    cv.frame(x + 12, y + 10, 84, 34, INK, 2)
    cv.triangle(x + 28, y + 44, x + 42, y + 44, x + 32, y + 56, PAPER)
    draw_text(cv, x + 22, y + 20, "NO", RED, 2)

def scene_grid(cv, x, y, w, h):
    """Ukraine: power pylon, lightning, dark windows."""
    cv.rect(x, y, w, h, (38, 40, 44))
    # city windows, mostly dark, a few lit
    for r in range(3):
        for c in range(5):
            wx = x + 10 + c * 34
            wy = y + h - 24 - r * 22
            cv.rect(wx, wy, 20, 14, (90, 90, 88) if (r + c) % 3 else (250, 210, 60))
    # pylon, right of centre
    px = x + w // 2 + 30
    cv.line(px - 34, y + h - 6, px, y + 10, PAPER, 4)
    cv.line(px + 34, y + h - 6, px, y + 10, PAPER, 4)
    cv.line(px - 44, y + 30, px + 44, y + 30, PAPER, 4)
    cv.line(px - 32, y + 50, px + 32, y + 50, PAPER, 4)
    # lightning bolt (red), far right
    bx = x + w - 34
    cv.triangle(bx, y + 8, bx + 22, y + 8, bx + 10, y + 34, RED)
    cv.triangle(bx + 10, y + 34, bx + 22, y + 8, bx + 18, y + 40, RED)
    cv.triangle(bx - 6, y + 40, bx + 18, y + 40, bx + 4, y + 66, RED)

def scene_gaza(cv, x, y, w, h):
    """Gaza: dove over rubble, cracked truce line."""
    cv.rect(x, y, w, h, (233, 228, 216))
    # dove
    dx, dy = x + w // 2, y + 28
    cv.circle(dx, dy, 15, PAPER)
    cv.circle(dx + 15, dy - 7, 7, PAPER)
    cv.triangle(dx + 21, dy - 11, dx + 30, dy - 7, dx + 21, dy - 3, RED)
    cv.triangle(dx - 13, dy - 5, dx - 36, dy - 22, dx - 27, dy + 2, PAPER)
    cv.triangle(dx - 9, dy + 7, dx - 30, dy + 26, dx - 5, dy + 12, PAPER)
    cv.circle(dx + 17, dy - 9, 2, INK)
    # olive branch
    cv.line(dx - 48, dy + 30, dx - 18, dy + 20, (60, 110, 60), 3)
    cv.circle(dx - 40, dy + 26, 5, (60, 110, 60))
    cv.circle(dx - 28, dy + 22, 5, (60, 110, 60))
    # rubble blocks along the bottom
    for i, (bx, bw, bh) in enumerate(((12, 44, 14), (62, 36, 10),
                                      (104, 50, 16), (160, 32, 10))):
        cv.rect(x + bx, y + h - 10 - bh, bw, bh, DARKGREY if i % 2 else INK)
    # cracked truce line just above the rubble
    cv.line(x + 8, y + h - 30, x + w // 2 - 8, y + h - 30, INK, 3)
    cv.line(x + w // 2 + 12, y + h - 30, x + w - 8, y + h - 30, INK, 3)
    cv.line(x + w // 2 - 8, y + h - 30, x + w // 2 + 4, y + h - 42, RED, 3)
    cv.line(x + w // 2 + 4, y + h - 42, x + w // 2 + 12, y + h - 30, RED, 3)

def scene_oil(cv, x, y, w, h):
    """Hormuz: tanker on waves, spiked mine, price tag."""
    cv.rect(x, y, w, h, (214, 224, 226))
    # waves
    for i in range(5):
        cv.line(x + 6 + i * 44, y + h - 12, x + 28 + i * 44, y + h - 12, INK, 3)
    # tanker, low and left
    sx, sy = x + 16, y + h - 40
    cv.rect(sx, sy, 130, 18, INK)
    cv.triangle(sx + 130, sy, sx + 150, sy + 9, sx + 130, sy + 18, INK)
    cv.rect(sx + 14, sy - 18, 100, 18, RED)
    cv.frame(sx + 14, sy - 18, 100, 18, INK, 2)
    # mine (spiked ball), top right
    mx, my = x + w - 42, y + 34
    cv.circle(mx, my, 13, INK)
    for a in range(8):
        ang = math.pi * 2 * a / 8
        cv.line(mx, my, int(mx + 21 * math.cos(ang)), int(my + 21 * math.sin(ang)), INK, 3)
    # price tag, top left
    cv.rect(x + 10, y + 10, 84, 26, PAPER)
    cv.frame(x + 10, y + 10, 84, 26, INK, 2)
    draw_text(cv, x + 18, y + 17, "$91", RED, 2)

def scene_sudan(cv, x, y, w, h):
    """Sudan: quadcopter drone over flat-roofed houses, harsh sun."""
    cv.rect(x, y, w, h, (240, 226, 196))
    cv.circle(x + w - 36, y + 28, 18, RED)
    # houses
    for i, (hx, hw, hh) in enumerate(((10, 54, 26), (70, 44, 20),
                                      (120, 58, 30), (184, 38, 18))):
        cv.rect(x + hx, y + h - 16 - hh, hw, hh, INK if i % 2 == 0 else DARKGREY)
        cv.rect(x + hx + 8, y + h - 16 - hh + 7, 9, 10, PAPER)
    # drone, upper centre
    dx, dy = x + w // 2, y + 30
    cv.rect(dx - 24, dy - 7, 48, 12, INK)
    cv.rect(dx - 7, dy - 3, 14, 18, DARKGREY)
    for ox in (-32, 32):
        cv.line(dx + ox - 11, dy - 11, dx + ox + 11, dy - 11, INK, 3)
        cv.circle(dx + ox, dy - 11, 4, RED)
    cv.line(dx, dy + 15, dx, dy + 28, INK, 2)
    cv.circle(dx, dy + 32, 4, RED)

def scene_mumbai(cv, x, y, w, h):
    """Mumbai: Gateway of India arch, candles."""
    cv.rect(x, y, w, h, (233, 228, 216))
    ax = x + w // 2
    # arch body + dome, scaled to the panel
    cv.rect(ax - 44, y + 18, 88, 56, INK)
    cv.circle(ax, y + 56, 26, PAPER)
    cv.rect(ax - 26, y + 56, 52, 18, (233, 228, 216))
    cv.circle(ax, y + 18, 14, INK)
    cv.rect(ax - 56, y + 74, 112, 6, INK)
    # candles flanking the arch
    for cx in (ax - 76, ax - 62, ax + 62, ax + 76):
        cv.rect(cx - 3, y + h - 22, 6, 14, PAPER)
        cv.frame(cx - 3, y + h - 22, 6, 14, INK, 1)
        cv.triangle(cx, y + h - 32, cx - 4, y + h - 22, cx + 4, y + h - 22, RED)

def scene_thanks(cv, x, y, w, h):
    """Thanksgiving: turkey pictogram, pumpkin, corn, autumn table."""
    cv.rect(x, y, w, h, (240, 226, 196))
    # table
    cv.rect(x + 8, y + h - 14, w - 16, 6, INK)
    # turkey: fanned tail behind the body
    tx, ty = x + w // 2 - 6, y + 52
    for a in range(-2, 3):
        ang = math.pi * (0.5 + a * 0.22)
        fx = int(tx + 32 * math.cos(ang))
        fy = int(ty - 8 + 32 * math.sin(ang))
        cv.line(tx, ty - 6, fx, fy, RED if a % 2 == 0 else INK, 5)
    cv.circle(tx, ty + 6, 20, (150, 90, 40))
    cv.circle(tx + 18, ty - 12, 10, (150, 90, 40))
    cv.triangle(tx + 27, ty - 14, tx + 36, ty - 10, tx + 27, ty - 6, RED)
    cv.circle(tx + 20, ty - 14, 2, INK)
    # pumpkin, left
    cv.circle(x + 28, y + h - 30, 12, (210, 110, 30))
    cv.rect(x + 25, y + h - 46, 6, 7, (60, 110, 60))
    # corn, right
    cv.rect(x + w - 42, y + h - 40, 13, 24, (230, 190, 60))
    cv.frame(x + w - 42, y + h - 40, 13, 24, INK, 2)

# -------------------------------------------------------------- page -----
STORIES = [
    # (scene, kicker, headline, body, source)
    ("pushback", "TRADE", "CHINA, EU PUSH BACK",
     "Beijing calls 'overcapacity' a false premise. Brussels says its 15% ceiling must hold.",
     "REUTERS / ASIA TODAY"),
    ("grid", "WAR IN UKRAINE", "GRID STILL DARK",
     "Overnight strikes cut power in five regions. Crews race to restore heat as winter bites.",
     "REUTERS"),
    ("gaza", "GAZA", "TRUCE UNDER STRAIN",
     "Strikes kill two Hamas security chiefs in two days. Peace board warns the deal may collapse.",
     "AL JAZEERA / AFP"),
    ("oil", "ENERGY", "OIL NEAR $91",
     "Six tankers hit mines in the Strait of Hormuz since Tuesday. Brent holds as Gulf exports recover.",
     "REUTERS / BLOOMBERG"),
    ("sudan", "SUDAN", "19 KILLED IN DRONE STRIKES",
     "RSF drones hit homes in Damazin, Blue Nile. Six women among the dead; 20 more wounded.",
     "REUTERS"),
    ("mumbai", "INDIA", "MUMBAI REMEMBERS 26/11",
     "Eighteen years on, the city honours 166 victims at the Gateway of India.",
     "PTI"),
    ("thanks", "AMERICA", "THANKSGIVING DAY",
     "Families gather across the US as markets pause for the holiday.",
     "AP"),
]

SCENES = {
    "taipei": scene_taipei, "pushback": scene_pushback, "grid": scene_grid,
    "gaza": scene_gaza, "oil": scene_oil, "sudan": scene_sudan,
    "mumbai": scene_mumbai, "thanks": scene_thanks,
}

def build():
    cv = Canvas(W, H, PAPER)
    cv.frame(0, 0, W, H, INK, 4)
    # ---- masthead ----
    cv.rect(12, 12, W - 24, 118, INK)
    draw_text(cv, W // 2, 30, "THE WORLD TODAY", PAPER, 6, align="center")
    cv.hline(24, 96, W - 48, RED, 4)
    draw_text(cv, W // 2, 106, "THURSDAY 26 NOVEMBER 2026", RED, 2, align="center")
    draw_text(cv, 24, 106, "NO. 1", PAPER, 1)
    draw_text(cv, W - 24, 106, "ONE DAY'S NEWS", PAPER, 1, align="right")
    # ---- lead story ----
    lx, ly, lw, lh = 24, 146, W - 48, 330
    cv.frame(lx, ly, lw, lh, INK, 2)
    SCENES["taipei"](cv, lx + 2, ly + 2, 560, lh - 4)
    tx = lx + 576
    tw = lw - 590
    draw_text(cv, tx, ly + 16, "LEAD  |  TRADE WAR", RED, 2)
    cv.hline(tx, ly + 42, tw, INK, 2)
    y = wrap_text(cv, tx, ly + 56, tw, "TAIPEI ANSWERS THE TARIFF SALVO", INK, 4, lh=40)
    y = wrap_text(cv, tx, y + 10, tw,
                  "Taipei is confident of keeping its agreed 15% rate as Washington proposes new duties of up to 40% on 14 partners. Hearings run into January.",
                  INK, 2, lh=21)
    draw_text(cv, tx, ly + lh - 24, "REUTERS", RED, 1)
    # ---- seven smaller stories ----
    gy = 492
    rows = [STORIES[:4], STORIES[4:]]
    row_h = [212, 212]
    for ri, row in enumerate(rows):
        n = len(row)
        gap = 12
        cw = (W - 48 - gap * (n - 1)) // n
        y = gy + ri * (row_h[ri] + 12)
        for ci, (scene, kicker, head, body, src) in enumerate(row):
            x = 24 + ci * (cw + gap)
            cv.frame(x, y, cw, row_h[ri], INK, 2)
            SCENES[scene](cv, x + 2, y + 2, cw - 4, 92)
            draw_text(cv, x + 10, y + 102, kicker, RED, 1)
            yy = wrap_text(cv, x + 10, y + 118, cw - 20, head, INK, 2, lh=18)
            wrap_text(cv, x + 10, yy + 4, cw - 20, body, DARKGREY, 1, lh=12)
            draw_text(cv, x + 10, y + row_h[ri] - 14, src, GREY, 1)
    # ---- footer ----
    fy = 492 + 212 + 12 + 212 + 12
    cv.hline(24, fy, W - 48, INK, 2)
    draw_text(cv, W // 2, fy + 10,
              "SOURCES: REUTERS - AP - AFP - AL JAZEERA - PTI - BLOOMBERG",
              INK, 1, align="center")
    draw_text(cv, W // 2, fy + 28,
              "THE WORLD TODAY - THURSDAY 26 NOVEMBER 2026 - ALL THE NEWS OF ONE DAY",
              GREY, 1, align="center")
    return cv

def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(outdir, exist_ok=True)
    cv = build()
    data = png_bytes(bytes(cv.buf), W, H)
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(data)

if __name__ == "__main__":
    main()
