"""Flat Zabbix map icon set generator.

Every icon is a function returning SVG body markup in its own coordinate
space (the 128-size pixel grid of the original Zabbix icon), so the
icons keep the exact aspect ratios of the originals.
"""
import math

# ---------------------------------------------------------------- palette
C = dict(
    red='#D40000', red_d='#A30000', red_l='#F2554D',
    blue='#0275B8', blue_d='#01588C', blue_l='#3FA0DC', blue_xl='#A8D4F2', blue_xxl='#D6ECFA',
    ink='#1A2328', slate_d='#232D33', slate='#2F3B42', slate_m='#3E4C55', slate_l='#556670', slate_xl='#7D909B',
    g1='#F5F7F8', g2='#E4E9EC', g3='#CBD4D9', g4='#A7B4BC', g5='#8798A2',
    green='#34B36A', green_l='#7FDCA4', amber='#F5A623', amber_l='#FFD36E', white='#FFFFFF',
    pcb='#23805A', pcb_d='#17603F', gold='#E2B045', gold_d='#B98A24',
)

LO = False  # low-detail mode, toggled by renderer for very small outputs


def f(v):
    return ('%.2f' % v).rstrip('0').rstrip('.')


def R(x, y, w, h, fill, rx=0, extra=''):
    return '<rect x="%s" y="%s" width="%s" height="%s"%s fill="%s"%s/>' % (
        f(x), f(y), f(w), f(h), (' rx="%s"' % f(rx)) if rx else '', fill, (' ' + extra) if extra else '')


def Cc(cx, cy, r, fill, extra=''):
    return '<circle cx="%s" cy="%s" r="%s" fill="%s"%s/>' % (f(cx), f(cy), f(r), fill, (' ' + extra) if extra else '')


def E(cx, cy, rx, ry, fill, extra=''):
    return '<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s"%s/>' % (
        f(cx), f(cy), f(rx), f(ry), fill, (' ' + extra) if extra else '')


def P(d, fill, extra=''):
    return '<path d="%s" fill="%s"%s/>' % (d, fill, (' ' + extra) if extra else '')


def G(pts, fill, extra=''):
    return '<polygon points="%s" fill="%s"%s/>' % (' '.join('%s,%s' % (f(a), f(b)) for a, b in pts), fill,
                                                     (' ' + extra) if extra else '')


def L(x1, y1, x2, y2, stroke, w, extra=''):
    return '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s" stroke-linecap="round"%s/>' % (
        f(x1), f(y1), f(x2), f(y2), stroke, f(w), (' ' + extra) if extra else '')


def PL(pts, stroke, w, extra=''):
    return '<polyline points="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" ' \
           'stroke-linejoin="round"%s/>' % (' '.join('%s,%s' % (f(a), f(b)) for a, b in pts), stroke, f(w),
                                            (' ' + extra) if extra else '')


def T(body, tx=0, ty=0, s=1.0, rot=0, cx=0, cy=0):
    t = 'translate(%s %s)' % (f(tx), f(ty))
    if rot:
        t += ' rotate(%s %s %s)' % (f(rot), f(cx), f(cy))
    if s != 1:
        t += ' scale(%s)' % f(s)
    return '<g transform="%s">%s</g>' % (t, body)


# ---------------------------------------------------------------- building blocks
def box(x, y, w, h, d, top, front, rx=3, k=0.55):
    """2.5D box: trapezoid top face (depth d) above a rounded front face."""
    s = G([(x + d * k, y), (x + w - d * k, y), (x + w, y + d), (x, y + d)], top)
    s += R(x, y + d, w, h, front, rx)
    s += R(x, y + d, w, min(3, h), front)  # square top corners of the front
    return s


def led(cx, cy, r, color):
    return Cc(cx, cy, r, color)


def zlogo(x, y, s, bg=None, fg=None):
    bg = bg or C['red']
    fg = fg or C['white']
    pts = [(0.2, 0.2), (0.8, 0.2), (0.8, 0.34), (0.4, 0.66), (0.8, 0.66), (0.8, 0.8), (0.2, 0.8), (0.2, 0.66),
           (0.6, 0.34), (0.2, 0.34)]
    return R(x, y, s, s, bg, s * 0.12) + G([(x + a * s, y + b * s) for a, b in pts], fg)


def padlock(cx, top, w):
    """Red padlock; top = y of shackle top, w = body width."""
    h = w * 0.82
    r = w * 0.3
    sw = w * 0.13
    by = top + r + w * 0.12
    s = P('M%s %s V%s A%s %s 0 0 1 %s %s V%s' % (f(cx - r), f(by + 2), f(top + r), f(r), f(r), f(cx + r), f(top + r),
                                              f(by + 2)), 'none',
          'stroke="%s" stroke-width="%s" stroke-linecap="round"' % (C['g4'], f(sw)))
    s += R(cx - w / 2, by, w, h, C['red'], w * 0.12)
    s += R(cx - w / 2, by + h * 0.62, w, h * 0.38, C['red_d'], w * 0.12)
    s += R(cx - w / 2, by + h * 0.62, w, h * 0.12, C['red_d'])
    s += Cc(cx, by + h * 0.38, w * 0.1, C['white'])
    s += R(cx - w * 0.04, by + h * 0.38, w * 0.08, h * 0.3, C['white'], w * 0.03)
    return s


def screen(x, y, w, h, base=None, hi=None):
    base = base or C['blue']
    hi = hi or C['blue_l']
    s = R(x, y, w, h, base)
    s += G([(x + w * 0.45, y), (x + w, y), (x + w, y + h * 0.55), (x + w * 0.75, y + h)], hi, 'opacity="0.55"')
    return s


def monitor(x, y, w, h, stand=True, content=None):
    b = max(2.5, w * 0.045)
    s = ''
    if stand:
        s += G([(x + w * 0.44, y + h - 2), (x + w * 0.56, y + h - 2), (x + w * 0.6, y + h + h * 0.16),
                (x + w * 0.4, y + h + h * 0.16)], C['g4'])
        s += R(x + w * 0.27, y + h + h * 0.14, w * 0.46, max(3, h * 0.07), C['g5'], 2)
    s += R(x, y, w, h, C['slate'], max(2, w * 0.05))
    s += content if content is not None else screen(x + b, y + b, w - 2 * b, h - 2 * b - b * 0.6)
    s += Cc(x + w / 2, y + h - b * 0.8, b * 0.25, C['slate_xl']) if not LO else ''
    return s


def keyboard(x, y, w, h):
    s = R(x, y, w, h, C['g3'], h * 0.18)
    s += R(x, y, w, h * 0.78, C['g2'], h * 0.18)
    if not LO:
        cols, rows = 12, 3
        kw = (w - 8) / cols
        kh = (h * 0.78 - 6) / rows
        for r in range(rows):
            for c in range(cols):
                if r == rows - 1 and 3 <= c <= 8:
                    continue
                s += R(x + 4 + c * kw + 0.6, y + 3 + r * kh + 0.5, kw - 1.2, kh - 1, C['g4'], 0.8)
        s += R(x + 4 + 3 * kw + 0.6, y + 3 + 2 * kh + 0.5, 6 * kw - 1.2, kh - 1, C['g4'], 0.8)
    return s


def tower(x, y, w, h, front=None, side=None, bays=3, button=None):
    front = front or C['slate']
    side = side or C['slate_d']
    d = w * 0.18
    s = G([(x + w - 2, y), (x + w + d, y + d * 0.5), (x + w + d, y + h - d * 0.5), (x + w - 2, y + h)], side)
    s += R(x, y, w, h, front, w * 0.08)
    bx, bw = x + w * 0.14, w * 0.72
    bh = h * 0.075
    for i in range(bays):
        by = y + h * 0.08 + i * bh * 1.35
        s += R(bx, by, bw, bh, C['slate_l'] if front != C['g2'] else C['g4'], bh * 0.2)
        if not LO:
            s += R(bx + bw * 0.08, by + bh * 0.4, bw * 0.5, bh * 0.2, C['slate_d'] if front != C['g2'] else C['g5'])
            s += led(bx + bw * 0.86, by + bh / 2, bh * 0.18, C['green'])
    vy = y + h * 0.08 + bays * bh * 1.35 + h * 0.06
    if not LO:
        for i in range(5):
            s += R(bx, vy + i * h * 0.05, bw, h * 0.022, C['slate_m'] if front != C['g2'] else C['g3'], h * 0.01)
    by = y + h * 0.82
    s += Cc(x + w / 2, by, w * 0.11, button or C['blue'])
    s += Cc(x + w / 2, by, w * 0.055, front)
    return s


def rackunit_front(x, y, w, h, units, kind='server'):
    """Front of a rackmountable device including the 19" ears."""
    ear = max(4, w * 0.04)
    s = R(x, y, ear + 2, h, C['slate_l'], 1.2)
    s += R(x + w - ear - 2, y, ear + 2, h, C['slate_l'], 1.2)
    if h >= 12 and not LO:
        for ey in ([y + h * 0.5] if h < 22 else [y + h * 0.25, y + h * 0.75]):
            s += R(x + ear * 0.25, ey - 1, ear * 0.5, 2, C['slate_d'], 1)
            s += R(x + w - ear * 0.75, ey - 1, ear * 0.5, 2, C['slate_d'], 1)
    bx, bw = x + ear, w - 2 * ear
    s += R(bx, y, bw, h, C['slate'])
    s += R(bx, y, bw, max(0.8, h * 0.06), C['slate_m'])
    pad = max(1, min(2.2, h * 0.12))
    iy, ih = y + pad, h - 2 * pad
    if kind in ('server', 'zabbix'):
        left = bx + 3
        if kind == 'zabbix':
            zs = min(ih, 16)
            s += zlogo(left, y + (h - zs) / 2, zs)
            left += zs + 3
        right_panel = bw * 0.22
        bays_w = bx + bw - right_panel - left - 2
        rows = max(1, min(units, 4))
        cols = 4 if units == 1 else (4 if units <= 2 else 3)
        cols = cols if kind == 'server' else 3
        cw = bays_w / cols
        rh = ih / rows
        for r in range(rows):
            for c in range(cols):
                cx0 = left + c * cw
                cy0 = iy + r * rh
                s += R(cx0 + 0.5, cy0 + 0.4, cw - 1, rh - 0.8, C['slate_l'], min(1.2, rh * 0.15))
                if rh >= 4 and not LO:
                    s += R(cx0 + 2, cy0 + rh * 0.42, cw * 0.55, max(0.6, rh * 0.16), C['slate_d'])
                    s += led(cx0 + cw - 3, cy0 + rh / 2, max(0.6, min(1.3, rh * 0.18)), C['green'])
        px = bx + bw - right_panel
        # control panel: vents + LEDs + power
        if not LO:
            vrows = max(1, int(ih // 3.2))
            for i in range(vrows):
                s += R(px + 1, iy + i * (ih / vrows) + 0.6, right_panel * 0.5, max(0.6, ih / vrows - 1.6),
                       C['slate_m'], 0.5)
        lr = max(0.7, min(1.6, ih * 0.16))
        s += led(px + right_panel * 0.68, y + h / 2, lr, C['blue_l'])
        s += led(px + right_panel * 0.86, y + h / 2, lr, C['green'])
    elif kind == 'disk':
        cols = 12
        left = bx + 3
        bays_w = bw * 0.84
        cw = bays_w / cols
        for c in range(cols):
            cx0 = left + c * cw
            s += R(cx0 + 0.6, iy, cw - 1.2, ih, C['slate_l'], 1)
            if not LO:
                s += R(cx0 + cw * 0.3, iy + ih * 0.15, cw * 0.4, ih * 0.5, C['slate_d'], 0.6)
                s += led(cx0 + cw / 2, iy + ih * 0.82, max(0.6, min(1.2, cw * 0.12)),
                         C['green'] if c % 5 else C['blue_l'])
        px = left + bays_w + 2
        s += led(px + (bx + bw - px) / 2, y + h * 0.35, max(0.7, h * 0.06), C['blue_l'])
        s += led(px + (bx + bw - px) / 2, y + h * 0.65, max(0.7, h * 0.06), C['green'])
    elif kind == 'ups':
        # LCD + warning badge + battery gauge
        s += R(bx + 4, iy + ih * 0.12, bw * 0.16, ih * 0.76, C['amber'], 1.5)
        if not LO:
            s += G([(bx + 4 + bw * 0.08, iy + ih * 0.25), (bx + 4 + bw * 0.035, iy + ih * 0.75),
                    (bx + 4 + bw * 0.125, iy + ih * 0.75)], C['slate'])
        s += R(bx + bw * 0.26, iy + ih * 0.2, bw * 0.2, ih * 0.6, C['blue_d'], 1)
        if not LO:
            s += R(bx + bw * 0.28, iy + ih * 0.35, bw * 0.12, ih * 0.12, C['blue_xl'])
            s += R(bx + bw * 0.28, iy + ih * 0.55, bw * 0.08, ih * 0.12, C['blue_xl'])
        gx, gw = bx + bw * 0.52, bw * 0.36
        s += R(gx, iy + ih * 0.1, gw, ih * 0.8, C['slate_d'], 1.5)
        s += R(gx + gw, iy + ih * 0.32, gw * 0.04, ih * 0.36, C['slate_d'])
        segs = 5
        sw = (gw - 3) / segs
        for i in range(segs):
            s += R(gx + 1.5 + i * sw + 0.5, iy + ih * 0.2, sw - 1, ih * 0.6, C['green'], 0.6)
        s += Cc(bx + bw * 0.95, y + h / 2, max(1, ih * 0.16), C['red'])
    return s


def rack3d(w, H, h2d, units, kind):
    t = H - h2d
    ear = max(4, w * 0.04)
    s = G([(ear + t * 0.9, 0), (w - ear - t * 0.9, 0), (w - ear, t), (ear, t)], C['slate_m'])
    s += G([(ear + t * 0.9, 0), (w - ear - t * 0.9, 0), (w - ear - t * 0.6, t * 0.3), (ear + t * 0.6, t * 0.3)],
           C['slate_l'], 'opacity="0.6"')
    s += rackunit_front(0, t, w, h2d, units, kind)
    return s


# ---------------------------------------------------------------- icons (128 grid)
def cloud():
    def shape(dy, fill):
        return ''.join([
            Cc(36, 40 + dy, 22, fill), Cc(62, 29 + dy, 25, fill), Cc(91, 35 + dy, 21, fill), Cc(107, 47 + dy, 15, fill),
            R(14, 38 + dy, 108, 24, fill, 12)])
    s = shape(4, C['blue_l'])
    s += shape(0, C['blue_xl'])
    s += P('M30 32 A14 14 0 0 1 48 22', 'none', 'stroke="%s" stroke-width="4" stroke-linecap="round"' % C['white'])
    s += P('M56 18 A16 16 0 0 1 76 12', 'none', 'stroke="%s" stroke-width="4" stroke-linecap="round" opacity="0.8"'
           % C['white'])
    return 128, 68, s


def flame(cx, base, w, h, outer, inner):
    def fp(cx, base, w, h):
        return 'M%s %s C%s %s %s %s %s %s C%s %s %s %s %s %s C%s %s %s %s %s %s Z' % (
            f(cx - w / 2), f(base),
            f(cx - w / 2), f(base - h * 0.45), f(cx - w * 0.15), f(base - h * 0.55), f(cx - w * 0.05), f(base - h),
            f(cx + w * 0.25), f(base - h * 0.7), f(cx + w * 0.55), f(base - h * 0.45), f(cx + w / 2), f(base - h * 0.15),
            f(cx + w * 0.45), f(base), f(cx + w * 0.2), f(base), f(cx - w / 2), f(base))
    return P(fp(cx, base, w, h), outer) + P(fp(cx + w * 0.04, base, w * 0.55, h * 0.6), inner)


def firewall():
    s = flame(30, 44, 30, 40, C['amber'], C['amber_l'])
    s += flame(64, 44, 40, 44, C['amber'], C['amber_l'])
    s += flame(98, 44, 30, 36, C['amber'], C['amber_l'])
    x0, y0, w, h = 6, 34, 116, 60
    s += R(x0, y0, w, h, '#F3D2CF', 4)
    rows = 5
    bh = h / rows
    for r in range(rows):
        off = 0 if r % 2 == 0 else -14
        x = x0 + off
        i = 0
        while x < x0 + w:
            bw = 28
            xa, xb = max(x, x0), min(x + bw, x0 + w)
            if xb - xa > 3:
                col = C['red'] if (i + r) % 3 else C['red_d']
                s += R(xa + 1.2, y0 + r * bh + 1.2, xb - xa - 2.4, bh - 2.4, col, 1.5)
            x += bw
            i += 1
    s += R(x0, y0, w, 3, C['red_d'], 1.5)
    return 128, 96, s


def house():
    s = R(80, 14, 13, 30, C['slate_m'], 1.5) + R(78, 12, 17, 6, C['slate'], 1.5)
    s += R(16, 54, 85, 70, C['g2'])
    s += R(16, 112, 85, 12, C['g3'])
    s += G([(58.5, 4), (115, 58), (105, 62), (58.5, 18), (12, 62), (2, 58)], C['red'])
    s += G([(58.5, 18), (105, 62), (12, 62)], C['g1'])
    s += G([(58.5, 18), (101, 58), (101, 64), (16, 64), (16, 58)], C['g3'], 'opacity="0.55"')
    s += R(44, 80, 24, 44, C['blue'], 2) + Cc(63, 104, 2, C['white'])
    s += R(76, 72, 18, 18, C['blue_l'], 2) + R(84, 72, 2, 18, C['white']) + R(76, 80, 18, 2, C['white'])
    s += R(24, 72, 14, 18, C['blue_l'], 2) + R(30, 72, 2, 18, C['white']) + R(24, 80, 14, 2, C['white'])
    s += Cc(58.5, 40, 6, C['blue_l']) + R(57.5, 34, 2, 12, C['white']) + R(52.5, 39, 12, 2, C['white'])
    return 117, 128, s


def netbox(x, y, w, h, d, top, front, ports, port_col, led_cols, port_h=None, two_rows=False, band=None):
    s = box(x, y, w, h, d, top, front)
    fy = y + d
    px0 = x + w * 0.1
    pw_total = w * (0.66 if band else 0.8)
    n = ports
    ph = port_h or h * 0.32
    if two_rows:
        ph = h * 0.22
        pw = pw_total / n
        for row in range(2):
            for i in range(n):
                xx = px0 + i * pw
                yy = fy + h * 0.22 + row * (ph + h * 0.12)
                s += R(xx + 1, yy, pw - 2, ph, port_col, 1)
                if not LO:
                    s += R(xx + pw * 0.3, yy + ph * 0.6, pw * 0.4 - 1, ph * 0.4, front)
                    s += led(xx + pw / 2, yy - h * 0.06, 1.1, led_cols[(i + row) % len(led_cols)])
    else:
        pw = pw_total / n
        for i in range(n):
            xx = px0 + i * pw
            yy = fy + h * 0.42
            s += R(xx + pw * 0.15, yy, pw * 0.7, ph, port_col, 1.5)
            if not LO:
                s += R(xx + pw * 0.38, yy + ph * 0.62, pw * 0.24, ph * 0.38, front)
            s += led(xx + pw / 2, fy + h * 0.24, max(1.2, h * 0.05), led_cols[i % len(led_cols)])
    if band:
        s += R(x + w * 0.8, fy + h * 0.18, w * 0.13, h * 0.64, band, 2)
        s += led(x + w * 0.865, fy + h * 0.5, max(1.3, h * 0.07), C['white'])
    return s


def hub():
    s = netbox(6, 14, 116, 42, 22, C['g2'], C['g3'], 4, C['slate'], [C['green'], C['green'], C['amber']],
               band=C['blue'])
    return 128, 80, s


def switch():
    s = netbox(4, 14, 120, 42, 22, C['slate_m'], C['slate'], 8, C['ink'], [C['green'], C['green'], C['amber']],
               two_rows=True, band=C['blue'])
    return 128, 80, s


def router_body(x, y, w, h, d):
    return netbox(x, y, w, h, d, C['blue_l'], C['blue'], 4, C['blue_d'], [C['green_l'], C['green_l'], C['amber_l']],
                  band=C['blue_d'])


def antenna(x, y1, y2, w=6):
    return R(x - w / 2, y1, w, y2 - y1, C['slate_m'], w / 2) + R(x - w / 2, y2 - 10, w, 10, C['slate'], 1)


def router():
    s = antenna(24, 4, 60) + antenna(104, 4, 60)
    s += router_body(6, 46, 116, 46, 24)
    return 128, 118, s


def crypto_router():
    s = antenna(104, 6, 64)
    s += padlock(52, 4, 32)
    s += router_body(6, 50, 116, 46, 24)
    return 128, 121, s


def arrow_pts(theta, r1, r2, w, head):
    ux, uy = math.cos(theta), math.sin(theta)
    nx, ny = -uy, ux
    hb = r2 - head if r2 > r1 else r2 + head
    sgn = 1 if r2 > r1 else -1
    pts = [
        (r1 * ux + nx * w / 2, r1 * uy + ny * w / 2),
        (hb * ux + nx * w / 2, hb * uy + ny * w / 2),
        (hb * ux + nx * head * 0.75, hb * uy + ny * head * 0.75),
        (r2 * ux, r2 * uy),
        (hb * ux - nx * head * 0.75, hb * uy - ny * head * 0.75),
        (hb * ux - nx * w / 2, hb * uy - ny * w / 2),
        (r1 * ux - nx * w / 2, r1 * uy - ny * w / 2),
    ]
    return pts


def cylinder(cx, top_cy, rx, ry, h, top, body, arrows=True):
    s = E(cx, top_cy + h, rx, ry, body)
    s += R(cx - rx, top_cy, 2 * rx, h, body)
    s += E(cx, top_cy, rx, ry, top)
    if arrows:
        g = ''
        rr = rx * 0.82
        for ang, inward in ((45, True), (225, True), (135, False), (315, False)):
            th = math.radians(ang)
            a, b = (rr, rr * 0.25) if inward else (rr * 0.25, rr)
            g += G(arrow_pts(th, a, b, rx * 0.13, rx * 0.26), C['white'])
        s += '<g transform="translate(%s %s) scale(1 %s)">%s</g>' % (f(cx), f(top_cy), f(ry / rx), g)
    return s


def router_symbol():
    return 128, 73, cylinder(64, 23, 58, 19, 28, C['blue_l'], C['blue'])


def crypto_router_symbol():
    s = padlock(64, 4, 40)
    s += cylinder(64, 77, 58, 19, 28, C['blue_l'], C['blue'])
    return 128, 127, s


def modem():
    s = box(6, 18, 116, 30, 26, C['g2'], C['g3'])
    fy = 44
    for i in range(6):
        s += R(18 + i * 11, fy + 11, 7, 3, C['green'] if i != 4 else C['amber'], 1.5)
    s += R(90, fy + 8, 22, 9, C['slate'], 2)
    if not LO:
        s += led(95, fy + 12.5, 1.6, C['blue_l'])
    s += R(6, fy + 26, 116, 4, C['g4'], 2)
    return 128, 77, s


def mini_monitor(x, y, w, h):
    return monitor(x, y, w, h)


def network():
    pts = [(64, 20), (24, 72), (104, 72)]
    s = PL([pts[0], pts[1], pts[2], pts[0]], C['blue_l'], 5)
    for (cx, cy) in pts:
        s += Cc(cx, cy, 5, C['blue_l'])
    s += monitor(42, 2, 44, 30)
    s += monitor(2, 56, 44, 30)
    s += monitor(82, 56, 44, 30)
    return 128, 102, s


def network_adapter():
    s = R(22, 28, 86, 74, C['pcb'], 4)
    s += R(22, 90, 86, 12, C['pcb_d'], 4) + R(22, 90, 86, 4, C['pcb_d'])
    # gold edge connector with notch
    s += R(36, 102, 44, 12, C['gold'], 1) + R(84, 102, 18, 12, C['gold'], 1)
    if not LO:
        for i in range(10):
            s += R(38 + i * 4.2, 104, 2, 9, C['gold_d'])
        for i in range(4):
            s += R(86 + i * 4, 104, 2, 9, C['gold_d'])
    s += R(56, 44, 28, 28, C['ink'], 3) + R(60, 48, 20, 20, C['slate'], 2)
    s += R(88, 40, 12, 8, C['ink'], 1) + R(88, 54, 12, 8, C['ink'], 1) + R(36, 76, 14, 8, C['ink'], 1)
    if not LO:
        for i in range(6):
            s += R(36, 38 + i * 6, 12, 2, C['green_l'], 1)
    # bracket
    s += G([(4, 6), (24, 6), (24, 14), (14, 14)], C['g4'])
    s += R(10, 6, 12, 112, C['g3'], 1.5)
    s += G([(10, 118), (22, 118), (18, 126), (14, 126)], C['g4'])
    s += R(11.5, 40, 9, 16, C['slate'], 1.5) + R(13.5, 52, 5, 3, C['slate_d'])
    s += led(16, 64, 2, C['green']) + led(16, 71, 2, C['amber'])
    return 113, 128, s


def notebook():
    s = R(16, 4, 96, 72, C['slate'], 6)
    s += screen(22, 10, 84, 60)
    s += G([(16, 76), (112, 76), (124, 106), (4, 106)], C['g3'])
    s += G([(24, 80), (104, 80), (110, 96), (18, 96)], C['g4'])
    if not LO:
        for r in range(3):
            y = 81.5 + r * 4.8
            xl = 24 - r * 2
            xr = 104 + r * 2
            n = 14
            kw = (xr - xl) / n
            for c in range(n):
                s += R(xl + c * kw + 0.5, y, kw - 1, 3.4, C['g2'], 0.6)
    s += R(54, 98, 20, 6, C['g4'], 1.5)
    s += R(2, 105, 124, 8, C['g4'], 4) + R(52, 105, 24, 3, C['g5'], 1.5)
    return 128, 117, s


def phone(dx=0, dy=0):
    s = G([(18, 30), (110, 30), (122, 82), (6, 82)], C['g2'], 'stroke="%s" stroke-width="6" stroke-linejoin="round"'
          % C['g2'])
    s += R(3, 76, 122, 12, C['g3'], 5)
    # handset
    s += R(14, 8, 100, 16, C['slate'], 8)
    s += E(24, 22, 16, 9, C['slate']) + E(104, 22, 16, 9, C['slate'])
    s += R(14, 8, 100, 5, C['slate_m'], 3)
    # display + keypad
    s += R(70, 38, 38, 16, C['slate'], 2) + R(72, 40, 34, 12, C['blue'])
    if not LO:
        s += R(74, 43, 18, 2.5, C['blue_xl']) + R(74, 47, 12, 2.5, C['blue_xl'])
    for r in range(4):
        for c in range(3):
            s += R(24 + c * 12, 38 + r * 9, 9, 6.5, C['slate_l'], 1.5)
    s += R(72, 60, 16, 7, C['green'], 2) + R(92, 60, 16, 7, C['red'], 2)
    return 128, 93, s


def pbx():
    s = tower(4, 4, 46, 116, C['g2'], C['g4'], bays=4, button=C['green'])
    _, _, ph = phone()
    s += T(ph, 42, 60, 0.67)
    return 128, 125, s


def ip_pbx():
    s = tower(4, 4, 44, 112, C['g2'], C['g4'], bays=4, button=C['green'])
    _, _, rt = router()
    s += T(rt, 62, 2, 0.48)
    _, _, ph = phone()
    s += T(ph, 42, 58, 0.66)
    return 128, 119, s


def ip_pbx_symbol():
    s = tower(4, 4, 44, 112, C['g2'], C['g4'], bays=4, button=C['green'])
    _, _, rs = router_symbol()
    s += T(rs, 64, 4, 0.46)
    _, _, ph = phone()
    s += T(ph, 42, 58, 0.66)
    return 128, 119, s


def printer():
    s = R(30, 4, 68, 40, C['white'], 2, 'stroke="%s" stroke-width="2"' % C['g3'])
    if not LO:
        for i in range(4):
            s += R(38, 12 + i * 7, 52 - (i % 2) * 14, 2.5, C['g3'], 1)
    s += box(6, 30, 116, 60, 16, C['g2'], C['g3'], 6)
    s += R(6, 72, 116, 18, C['slate_m'], 6) + R(6, 72, 116, 6, C['slate_m'])
    s += R(22, 80, 84, 5, C['ink'], 2)
    s += R(90, 52, 24, 10, C['slate'], 2) + led(96, 57, 2, C['green']) + led(103, 57, 2, C['blue_l'])
    s += G([(26, 83), (102, 83), (106, 116), (22, 116)], C['white'], 'stroke="%s" stroke-width="2" '
           'stroke-linejoin="round"' % C['g3'])
    if not LO:
        for i in range(3):
            s += R(34, 92 + i * 7, 56 - (i % 2) * 18, 2.5, C['g3'], 1)
    return 128, 119, s


def rack_body(x, y, w, h, units=42, u=9.0):
    """Front of a 42U rack. Interior aligned so 128-wide rack units fit over posts."""
    s = R(x + 8, y + h - 2, 14, 10, C['slate_d'], 2) + R(x + w - 22, y + h - 2, 14, 10, C['slate_d'], 2)
    s += Cc(x + 15, y + h + 10, 6, C['ink']) + Cc(x + w - 15, y + h + 10, 6, C['ink'])
    s += Cc(x + 15, y + h + 10, 2.5, C['slate_l']) + Cc(x + w - 15, y + h + 10, 2.5, C['slate_l'])
    s += R(x, y, w, h, C['slate'], 5)
    s += R(x + 4, y + 4, w - 8, 16, C['slate_m'], 3)
    if not LO:
        for i in range(10):
            s += R(x + 14 + i * ((w - 28) / 10), y + 9, (w - 28) / 10 - 3, 6, C['slate'], 1.5)
    top = y + 24
    inner_h = units * u
    post = 11
    s += R(x + 3, top, w - 6, inner_h, C['slate_d'])
    s += R(x + 3 + post, top, w - 6 - 2 * post, inner_h, '#45545D')
    if not LO:
        for i in range(0, units, 2):
            s += R(x + 3 + post + 4, top + i * u + 2, w - 6 - 2 * post - 8, u * 2 - 4, '#3E4C55', 1.5)
    s += R(x + 3, top, post, inner_h, C['slate_l'])
    s += R(x + w - 3 - post, top, post, inner_h, C['slate_l'])
    if not LO:
        for i in range(units):
            yy = top + i * u + u / 2 - 1
            s += R(x + 6, yy, 4, 2, C['slate_d'], 1) + R(x + w - 10, yy, 4, 2, C['slate_d'], 1)
    s += R(x + 4, top + inner_h, w - 8, h - (top - y) - inner_h - 4, C['slate_m'], 3)
    return s


def rack_42():
    return 134, 435, rack_body(0, 0, 134, 418)


def rack_42_with_door():
    s = rack_body(0, 2, 134, 420)
    # open door hinged on the right side, seen in perspective
    s += G([(131, 6), (197, 0), (197, 440), (131, 424)], C['slate'])
    s += G([(138, 18), (190, 12), (190, 428), (138, 412)], C['blue_xl'], 'opacity="0.75"')
    s += G([(138, 18), (190, 12), (190, 60), (138, 150)], C['white'], 'opacity="0.35"')
    s += G([(183, 190), (190, 189), (190, 230), (183, 230)], C['g4'])
    return 199, 440, s


def rm_factory(units, three_d, kind='server'):
    h2 = {1: 9, 2: 17, 3: 26, 4: 35, 5: 44}[units]
    h3 = {1: 18, 2: 27, 3: 35, 4: 44, 5: 53}[units]

    def fn():
        if three_d:
            return 128, h3, rack3d(128, h3, h2, units, kind)
        return 128, h2, rackunit_front(0, 0, 128, h2, units, kind)
    return fn


def disk_array_2d():
    return 128, 24, rackunit_front(0, 0, 128, 24, 2, 'disk')


def disk_array_3d():
    return 128, 32, rack3d(128, 32, 24, 2, 'disk')


def ups_rm_2d():
    return 128, 26, rackunit_front(0, 0, 128, 26, 3, 'ups')


def ups_rm_3d():
    return 128, 35, rack3d(128, 35, 26, 3, 'ups')


def zabbix_2d():
    return 128, 17, rackunit_front(0, 0, 128, 17, 2, 'zabbix')


def zabbix_3d():
    return 128, 27, rack3d(128, 27, 17, 2, 'zabbix')


def san():
    s = PL([(64, 52), (64, 64), (26, 64), (26, 80)], C['red'], 2.5)
    s += PL([(64, 64), (102, 64), (102, 80)], C['red'], 2.5)
    for i in range(3):
        s += rack3d_scaled(30, 2 + i * 17, 68, 17)
    _, _, sw = switch()
    s += T(sw, 2, 74, 0.38)
    s += T(sw, 78, 74, 0.38)
    return 128, 107, s


def rack3d_scaled(x, y, w, h):
    return T(rack3d(128, 27, 17, 2, 'disk'), x, y, w / 128.0)


def satellite():
    g = ''
    for px in (4, 82):
        g += R(px, 28, 42, 22, C['blue_d'], 2)
        for i in range(1, 4):
            g += R(px + i * 10.5 - 0.6, 28, 1.2, 22, C['blue_l'])
        g += R(px, 38.4, 42, 1.2, C['blue_l'])
    g += R(46, 37, 36, 4, C['g4'])
    g += R(52, 20, 24, 36, C['gold'], 3) + R(52, 20, 24, 8, C['gold_d'], 3) + R(52, 24, 24, 4, C['gold_d'])
    g += R(56, 32, 16, 3, C['gold_d'], 1) + R(56, 40, 16, 3, C['gold_d'], 1)
    g += R(62, 56, 4, 6, C['g5']) + E(64, 66, 12, 5, C['g3']) + E(64, 65, 8, 3, C['g4'])
    g += L(64, 20, 64, 8, C['g5'], 2) + Cc(64, 7, 3, C['red'])
    return 128, 78, '<g transform="rotate(-10 64 39)">%s</g>' % g


def satellite_antenna():
    s = PL([(46, 84), (16, 124)], C['slate_m'], 6) + PL([(46, 84), (76, 124)], C['slate_m'], 6)
    s += R(42, 70, 8, 56, C['slate'], 3)
    s += R(10, 120, 72, 6, C['slate'], 3)
    dish = E(0, 0, 40, 18, C['g3']) + E(0, 2, 34, 13, C['g2']) + E(0, 4, 20, 7, C['g1'])
    s += '<g transform="translate(44 44) rotate(-35)">%s%s%s</g>' % (
        dish, L(0, 4, 0, -34, C['g5'], 3), R(-5, -42, 10, 10, C['red'], 2))
    s += Cc(46, 70, 6, C['slate_m'])
    return 92, 128, s


def server():
    return 96, 128, tower(8, 4, 66, 120, bays=3)


def ups():
    s = ''
    x, y, w, h = 8, 4, 72, 120
    d = w * 0.18
    s += G([(x + w - 2, y), (x + w + d, y + d * 0.5), (x + w + d, y + h - d * 0.5), (x + w - 2, y + h)], C['slate_d'])
    s += R(x, y, w, h, C['slate'], 6)
    s += R(x + 10, y + 12, w - 20, 26, C['slate_d'], 3)
    s += R(x + 14, y + 16, w - 28, 18, C['blue_d'], 2)
    gx, gw = x + 18, w - 40
    s += R(gx, y + 20, gw, 10, C['slate_d'], 1.5) + R(gx + gw, y + 23, 3, 4, C['slate_d'])
    for i in range(4):
        s += R(gx + 1.5 + i * (gw - 3) / 4 + 0.5, y + 21.5, (gw - 3) / 4 - 1, 7, C['green'], 0.8)
    cx, cy = x + w / 2, y + 62
    s += Cc(cx, cy, 11, C['red'])
    s += P('M%s %s A6 6 0 1 0 %s %s' % (f(cx - 4), f(cy - 4.5), f(cx + 4), f(cy - 4.5)), 'none',
           'stroke="%s" stroke-width="2.4" stroke-linecap="round"' % C['white'])
    s += L(cx, cy - 8, cx, cy - 1, C['white'], 2.4)
    s += Cc(cx, cy + 22, 6, C['slate_l']) + Cc(cx, cy + 22, 3, C['amber'])
    if not LO:
        for i in range(4):
            s += R(x + 14, y + 98 + i * 5, w - 28, 2.2, C['slate_m'], 1)
    return 99, 128, s


def person(cx, top, sz, skin, shirt):
    return E(cx, top + sz * 1.05, sz * 0.75, sz * 0.5, shirt) + Cc(cx, top + sz * 0.32, sz * 0.3, skin)


def video_terminal():
    s = ''
    bg = [C['blue'], C['blue_d'], C['blue_d'], C['blue']]
    content = R(12, 22, 88, 58, C['blue_d'])
    tiles = ''
    for i in range(4):
        tx = 13 + (i % 2) * 44
        ty = 23 + (i // 2) * 28.5
        tiles += R(tx, ty, 42, 27.5, bg[i], 1.5)
        tiles += '<g>%s</g>' % person(tx + 21, ty + 6, 18, ['#F2C9A0', '#C68A5E', '#E8B48A', '#8D5B3A'][i],
                                      [C['g2'], C['red'], C['amber'], C['green']][i])
    content += '<clipPath id="vt"><rect x="12" y="22" width="88" height="58"/></clipPath><g clip-path="url(#vt)">' \
               + tiles + '</g>'
    s += monitor(6, 16, 100, 70, content=content)
    s += R(50, 6, 12, 12, C['slate'], 6) + Cc(56, 12, 3.5, C['blue_l']) + R(54, 16, 4, 3, C['slate'])
    # headset
    s += P('M84 112 A18 18 0 0 1 120 112', 'none', 'stroke="%s" stroke-width="4" stroke-linecap="round"' % C['slate'])
    s += R(78, 106, 12, 18, C['slate'], 5) + R(114, 106, 9, 18, C['slate'], 4)
    s += P('M86 122 Q 92 128 104 124', 'none', 'stroke="%s" stroke-width="2.5" stroke-linecap="round"' % C['slate_l'])
    s += Cc(105, 124, 2.5, C['red'])
    return 123, 128, s


def workstation():
    s = monitor(4, 6, 84, 64)
    s += tower(93, 12, 28, 94, C['g2'], C['g4'], bays=2, button=C['green'])
    s += keyboard(4, 94, 84, 20)
    return 128, 117, s


MODERN = {
    'Cloud': cloud, 'Crypto-router': crypto_router, 'Crypto-router_symbol': crypto_router_symbol,
    'Disk_array_2D': disk_array_2d, 'Disk_array_3D': disk_array_3d, 'Firewall': firewall, 'House': house,
    'Hub': hub, 'IP_PBX': ip_pbx, 'IP_PBX_symbol': ip_pbx_symbol, 'Modem': modem, 'Network': network,
    'Network_adapter': network_adapter, 'Notebook': notebook, 'PBX': pbx, 'Phone': phone, 'Printer': printer,
    'Router': router, 'Router_symbol': router_symbol, 'SAN': san, 'Satellite': satellite,
    'Satellite_antenna': satellite_antenna, 'Server': server, 'Switch': switch, 'UPS': ups,
    'UPS_rackmountable_2D': ups_rm_2d, 'UPS_rackmountable_3D': ups_rm_3d, 'Video_terminal': video_terminal,
    'Workstation': workstation, 'Zabbix_server_2D': zabbix_2d, 'Zabbix_server_3D': zabbix_3d,
}
for _u in range(1, 6):
    MODERN['Rackmountable_%dU_server_2D' % _u] = rm_factory(_u, False)
    MODERN['Rackmountable_%dU_server_3D' % _u] = rm_factory(_u, True)

RACKS = {'Rack_42': rack_42, 'Rack_42_with_door': rack_42_with_door}

CLASSIC = ['Hub', 'Network', 'Notebook', 'Phone', 'Printer', 'Router', 'Satellite', 'Server', 'UPS', 'Workstation']


def svg_doc(w, h, body, vb=None):
    vb = vb or (0, 0, w, h)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" viewBox="%s %s %s %s">%s</svg>\n'
            % (f(w), f(h), f(vb[0]), f(vb[1]), f(vb[2]), f(vb[3]), body))


def icon_svg(name, lo=False):
    global LO
    LO = lo
    fn = MODERN.get(name) or RACKS.get(name)
    w, h, body = fn()
    LO = False
    return svg_doc(w, h, body)


def classic_svg(name, lo=False):
    """Classic icons: the modern drawing centred in a square canvas."""
    global LO
    LO = lo
    w, h, body = MODERN[name]()
    LO = False
    side = max(w, h) * 1.08
    return svg_doc(side, side, body, (-(side - w) / 2, -(side - h) / 2, side, side))
