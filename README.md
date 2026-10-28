# zabbix-map-icons
The Zabbix icon pack with modernized version of default Zabbix map icons and a script to quickly replace them.


# Zabbix map icons — flat redesign

These files are a drop-in replacement for `misc/images/` and `database/*/images.sql`.

I’ve written zabbix_import_map_icons.py, which uploads the new icons through the Zabbix API and replaces the existing images with the same names. 

How it works

**Matching:** each image is named after its file, without .png. Server_(64).png becomes Server_(64).<br/>
**Existing images:** the picture is replaced but the image ID stays the same. Maps and icon maps that use those icons keep working and show the new picture.<br/>
**Missing images:** they are created as new icons. Add --no-create to only replace.<br/>
**Source:** you can point it at the zip itself (it reads png_modern/ inside) or at any folder of PNGs.<br/>
**Login:** use an API token with --token (recommended) or --user/--password. The user must be a Super admin, because the 8.0 code only lets that user type create or update images. The token is sent the way 8.0 expects it, as an Authorization: Bearer header.<br/>
**Requirements:** Python 3.8 or newer, zabbix-utils library and nothing else to install.<br/>

Options worth knowing:

**--dry-run** shows what would be replaced or created without changing anything.<br/>
**--backup DIR** saves the current version of each image before replacing it. To roll back, run the script again with **--source DIR --no-create**. Later runs never overwrite files already in the backup folder, so the original versions are kept.<br/>
Images that are already identical are skipped, so running it twice is safe.<br/>
If a name exists as a background image rather than an icon, the script reports it and leaves it alone.<br/>
If one image in a batch fails, the others in that batch still go through, and each failure is listed at the end.<br/>

Typical use

```
./zabbix_import_map_icons.py --url https://zabbix.example.com --token "$ZABBIX_API_TOKEN" \
    --source zabbix_flat_map_icons.zip --dry-run
```
```
./zabbix_import_map_icons.py --url https://zabbix.example.com --token "$ZABBIX_API_TOKEN" \
    --source zabbix_flat_map_icons.zip --backup ./icons_backup
```

To also add the classic icons, run it with --source <folder>/png_classic pointing at a folder you’ve unzipped. Those names aren’t built into Zabbix, so they’ll be created as new icons.

Added an archive with Haloween icons 🎃
