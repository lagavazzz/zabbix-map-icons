import os, re, sys, glob, io
import cairosvg
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
import icons

W = os.path.dirname(os.path.abspath(__file__))
ORIG = os.path.join(W, '..', 'orig')
CLASSIC_ORIG = '/mnt/user-data/uploads/zabbix-master/misc/images/png_classic'
OUT = os.path.join(W, 'out')
for d in ('png_modern', 'png_classic', 'svg/elements', 'svg/equipment_rack', 'svg/classic'):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)


def render(svg, w, h, path):
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=w, output_height=h)
    im = Image.open(io.BytesIO(png)).convert('RGBA')
    assert im.size == (w, h), (path, im.size, (w, h))
    im.save(path, optimize=True)


# SVG sources
for name in icons.MODERN:
    open(os.path.join(OUT, 'svg/elements', name + '.svg'), 'w').write(icons.icon_svg(name))
for name in icons.RACKS:
    open(os.path.join(OUT, 'svg/equipment_rack', name + '.svg'), 'w').write(icons.icon_svg(name))
for name in icons.CLASSIC:
    open(os.path.join(OUT, 'svg/classic', name + '.svg'), 'w').write(icons.classic_svg(name))

# modern PNGs: same names and pixel dimensions as the originals
n = 0
for p in sorted(glob.glob(os.path.join(ORIG, '*.png'))):
    fn = os.path.basename(p)[:-4]
    m = re.match(r'(.+)_\((\d+)\)$', fn)
    base = m.group(1)
    w, h = Image.open(p).size
    lo = max(w, h) <= 32
    render(icons.icon_svg(base, lo), w, h, os.path.join(OUT, 'png_modern', fn + '.png'))
    n += 1
print('modern', n)

# classic PNGs
n = 0
for p in sorted(glob.glob(os.path.join(CLASSIC_ORIG, '*.png'))):
    fn = os.path.basename(p)[:-4]
    base = fn[:-6] if fn.endswith('_small') else fn
    w, h = Image.open(p).size
    render(icons.classic_svg(base, max(w, h) <= 32), w, h, os.path.join(OUT, 'png_classic', fn + '.png'))
    n += 1
print('classic', n)
