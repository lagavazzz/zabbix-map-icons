"""Generate images.sql (fresh install) and update_images.sql (existing installs)
for MySQL and PostgreSQL, keeping the original imageid <-> name mapping."""
import os, re

W = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(W, 'out')
ORIG_SQL = '/mnt/user-data/uploads/zabbix-master/database/mysql/images.sql'

mapping = []
for line in open(ORIG_SQL):
    m = re.search(r"VALUES \((\d+),1,'([^']*)',0x", line)
    mapping.append((int(m.group(1)), m.group(2)))

for db in ('mysql', 'postgresql'):
    os.makedirs(os.path.join(OUT, 'database', db), exist_ok=True)

ins_my, ins_pg, up_my, up_pg = [], [], [], []
for iid, name in mapping:
    data = open(os.path.join(OUT, 'png_modern', name + '.png'), 'rb').read().hex().upper()
    ins_my.append("INSERT INTO `images` (`imageid`,`imagetype`,`name`,`image`) VALUES (%d,1,'%s',0x%s);" % (iid, name, data))
    ins_pg.append("INSERT INTO images (imageid,imagetype,name,image) VALUES (%d,1,'%s',decode('%s','hex'));" % (iid, name, data))
    up_my.append("UPDATE `images` SET `image`=0x%s WHERE `name`='%s' AND `imagetype`=1;" % (data, name))
    up_pg.append("UPDATE images SET image=decode('%s','hex') WHERE name='%s' AND imagetype=1;" % (data, name))

hdr = ('-- Replaces the built-in Zabbix map icons with the flat icon set.\n'
       '-- Only rows matching the original built-in icon names are touched; custom images are left as they are.\n'
       '-- Back up the images table before running.\n')
open(os.path.join(OUT, 'database/mysql/images.sql'), 'w').write('\n'.join(ins_my) + '\n')
open(os.path.join(OUT, 'database/postgresql/images.sql'), 'w').write('\n'.join(ins_pg) + '\n')
open(os.path.join(OUT, 'database/mysql/update_images.sql'), 'w').write(hdr + 'START TRANSACTION;\n' + '\n'.join(up_my) + '\nCOMMIT;\n')
open(os.path.join(OUT, 'database/postgresql/update_images.sql'), 'w').write(hdr + 'BEGIN;\n' + '\n'.join(up_pg) + '\nCOMMIT;\n')
print(len(mapping), 'rows')
