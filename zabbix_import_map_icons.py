#!/usr/bin/env python3
"""
Import PNG map icons into Zabbix through the API, using the official
zabbix_utils library (https://github.com/zabbix/python-zabbix-utils).

For every PNG file in the source, the image name is the file name without
".png" (for example "Server_(64).png" -> "Server_(64)"):

  * an existing image with that name gets its picture replaced (image.update),
    keeping its imageid, so maps and icon maps that use it keep working;
  * a missing image is created (image.create), unless --no-create is given.

The source can be a folder of PNG files or the zabbix_flat_map_icons.zip
archive (the png_modern/ folder inside it is used by default).

Requirements: Python 3.8+ and zabbix_utils (pip install zabbix_utils).
The API user must be a Super admin (image.create and image.update need that
user type). Authentication uses an API token (recommended) or a username and
password.

zabbix_utils refuses to talk to Zabbix versions newer than the ones it was
tested with (2.0.x: up to 7.4). For Zabbix 8.0 add --skip-version-check.

Examples:
  # see what would change, nothing is written
  ./zabbix_import_map_icons.py --url https://zabbix.example.com \\
      --token "$ZABBIX_TOKEN" --source zabbix_flat_map_icons.zip --dry-run

  # replace the built-in icons, keeping a backup of the current ones
  ./zabbix_import_map_icons.py --url https://zabbix.example.com \\
      --token "$ZABBIX_TOKEN" --source zabbix_flat_map_icons.zip \\
      --backup ./icons_backup --skip-version-check

  # roll back from that backup
  ./zabbix_import_map_icons.py --url https://zabbix.example.com \\
      --token "$ZABBIX_TOKEN" --source ./icons_backup --no-create
"""
import argparse
import base64
import getpass
import os
import ssl
import sys
import zipfile

try:
    from zabbix_utils import ZabbixAPI, APIRequestError, APINotSupported, ProcessingError
except ImportError:
    sys.exit('The zabbix_utils library is required: pip install zabbix_utils')

IMAGE_TYPE = {'icon': 1, 'background': 2}
PNG_MAGIC = b'\x89PNG\r\n\x1a\n'
API_ERRORS = (APIRequestError, ProcessingError)


def load_source(path, subdir):
    """Return {image name: PNG bytes} from a folder or a zip archive."""
    images = {}
    if os.path.isdir(path):
        for fn in sorted(os.listdir(path)):
            full = os.path.join(path, fn)
            if fn.lower().endswith('.png') and os.path.isfile(full):
                with open(full, 'rb') as fh:
                    images[fn[:-4]] = fh.read()
    elif zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            wanted = [m for m in zf.namelist()
                      if m.lower().endswith('.png') and os.path.basename(os.path.dirname(m)) == subdir]
            if not wanted:
                sys.exit('No PNG files in a "%s/" folder inside %s' % (subdir, path))
            for m in sorted(wanted):
                images[os.path.basename(m)[:-4]] = zf.read(m)
    else:
        sys.exit('Source not found or not a folder/zip: %s' % path)

    if not images:
        sys.exit('No PNG files found in %s' % path)
    bad = [n for n, data in images.items() if not data.startswith(PNG_MAGIC)]
    if bad:
        sys.exit('Not PNG files: %s' % ', '.join(bad))
    too_long = [n for n in images if len(n) > 64]
    if too_long:
        sys.exit('Image names longer than 64 characters: %s' % ', '.join(too_long))
    return images


def chunks(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def run_batches(method, objects, batch, labels):
    """Call an API method (e.g. api.image.update) in batches.

    A failed batch is retried one object at a time, so one bad image does not
    block the rest and every failure is reported by name.
    """
    done, failed = 0, []
    name_of = lambda o: o.get('name') or labels.get(o.get('imageid'), o.get('imageid'))
    for part in chunks(objects, batch):
        try:
            method(part)
            done += len(part)
        except API_ERRORS:
            for obj in part:
                try:
                    method([obj])
                    done += 1
                except API_ERRORS as e:
                    failed.append((name_of(obj), str(e)))
        print('  %d/%d' % (done + len(failed), len(objects)), end='\r', flush=True)
    if objects:
        print()
    return done, failed


def connect(args):
    ssl_context = ssl.create_default_context(cafile=args.cacert) if args.cacert else None
    api = ZabbixAPI(url=args.url, skip_version_check=args.skip_version_check,
                    validate_certs=not args.insecure, ssl_context=ssl_context, timeout=args.timeout)
    if args.token:
        api.login(token=args.token)
    else:
        api.login(user=args.user, password=args.password)
    return api


def main():
    ap = argparse.ArgumentParser(description='Import PNG map icons into Zabbix, replacing existing images by name.',
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog='Examples:' + __doc__.split('Examples:')[1])
    ap.add_argument('--url', default=os.environ.get('ZABBIX_URL'),
                    help='Zabbix frontend URL, e.g. https://zabbix.example.com (env ZABBIX_URL)')
    ap.add_argument('--token', default=os.environ.get('ZABBIX_TOKEN'),
                    help='API token of a Super admin user (env ZABBIX_TOKEN)')
    ap.add_argument('--user', default=os.environ.get('ZABBIX_USER'),
                    help='username, used when no token is given (env ZABBIX_USER)')
    ap.add_argument('--password', default=os.environ.get('ZABBIX_PASSWORD'),
                    help='password (env ZABBIX_PASSWORD; prompted if missing)')
    ap.add_argument('--source', required=True, help='folder with PNG files, or zabbix_flat_map_icons.zip')
    ap.add_argument('--zip-dir', default='png_modern', help='folder inside the zip to import (default: png_modern)')
    ap.add_argument('--type', choices=IMAGE_TYPE, default='icon',
                    help='image type to replace and to create (default: icon)')
    ap.add_argument('--no-create', action='store_true', help='only replace existing images, never create new ones')
    ap.add_argument('--backup', metavar='DIR',
                    help='save the current version of every image about to be replaced into DIR as PNG files '
                         '(existing files in DIR are never overwritten)')
    ap.add_argument('--dry-run', action='store_true', help='show what would change without writing anything')
    ap.add_argument('--batch', type=int, default=10, help='images per API request (default: 10)')
    ap.add_argument('--timeout', type=int, default=60, help='HTTP timeout in seconds (default: 60)')
    ap.add_argument('--skip-version-check', action='store_true',
                    help='let zabbix_utils work with Zabbix versions it was not tested with (needed for 8.0)')
    ap.add_argument('--cacert', help='CA bundle for HTTPS verification')
    ap.add_argument('--insecure', action='store_true', help='do not verify the HTTPS certificate')
    args = ap.parse_args()

    if not args.url:
        ap.error('--url (or ZABBIX_URL) is required')
    if not args.token and not args.user:
        ap.error('give --token (recommended) or --user/--password')
    if not args.token and not args.password:
        args.password = getpass.getpass('Password for %s: ' % args.user)
    if args.batch < 1:
        ap.error('--batch must be 1 or more')

    images = load_source(args.source, args.zip_dir)
    print('Source: %d PNG files from %s' % (len(images), args.source))

    try:
        api = connect(args)
    except APINotSupported as e:
        print('Error: %s' % e, file=sys.stderr)
        if 'not tested' in str(e) or 'not supported by the library' in str(e):
            print('Re-run with --skip-version-check to continue anyway.', file=sys.stderr)
        return 2
    except API_ERRORS as e:
        print('Error: cannot log in: %s' % e, file=sys.stderr)
        return 2

    try:
        print('Zabbix API %s at %s' % (api.version, api.url))
        want_type = IMAGE_TYPE[args.type]
        names = sorted(images)

        existing = {}
        for part in chunks(names, 500):
            for img in api.image.get(output=['imageid', 'imagetype', 'name'], filter={'name': part}):
                existing[img['name']] = img

        to_update, to_create, wrong_type = [], [], []
        for name in names:
            img = existing.get(name)
            if img is None:
                if not args.no_create:
                    to_create.append(name)
            elif int(img['imagetype']) != want_type:
                # image names are unique across both types; replacing a background with an icon
                # (or the other way round) is rarely intended, so these are reported and left alone
                wrong_type.append(name)
            else:
                to_update.append(name)

        # fetch the current pictures: to skip identical ones and to write the backup
        unchanged, backed_up = [], 0
        if to_update:
            ids = {existing[n]['imageid']: n for n in to_update}
            if args.backup and not args.dry_run:
                os.makedirs(args.backup, exist_ok=True)
            current = {}
            for part in chunks(list(ids), args.batch * 5):
                for img in api.image.get(output=['imageid', 'name'], imageids=part, select_image=True):
                    current[img['imageid']] = base64.b64decode(img.get('image') or '')
            for iid, name in ids.items():
                old = current.get(iid, b'')
                if old == images[name]:
                    unchanged.append(name)
                    continue
                if args.backup and not args.dry_run and old:
                    bpath = os.path.join(args.backup, name + '.png')
                    if not os.path.exists(bpath):  # keep the oldest (original) version
                        with open(bpath, 'wb') as fh:
                            fh.write(old)
                        backed_up += 1
            to_update = [n for n in to_update if n not in unchanged]

        print('Plan: %d to replace, %d to create, %d already identical, %d skipped (other image type)'
              % (len(to_update), len(to_create), len(unchanged), len(wrong_type)))
        type_name = {v: k for k, v in IMAGE_TYPE.items()}
        for name in wrong_type:
            print('  skipped, exists as type "%s": %s' % (type_name.get(int(existing[name]['imagetype'])), name))
        if args.no_create:
            missing = [n for n in names if n not in existing]
            if missing:
                print('  not in Zabbix, not created (--no-create): %d, e.g. %s' % (len(missing), missing[0]))

        if args.dry_run:
            for n in to_update:
                print('  would replace: %s (imageid %s)' % (n, existing[n]['imageid']))
            for n in to_create:
                print('  would create:  %s' % n)
            print('Dry run: nothing was changed.')
            return 0

        if backed_up:
            print('Backup: %d current images saved to %s' % (backed_up, os.path.abspath(args.backup)))

        b64 = lambda n: base64.b64encode(images[n]).decode()
        labels = {existing[n]['imageid']: n for n in to_update}

        if to_update:
            print('Replacing images...')
        upd_ok, upd_fail = run_batches(api.image.update,
                                       [{'imageid': existing[n]['imageid'], 'image': b64(n)} for n in to_update],
                                       args.batch, labels)
        if to_create:
            print('Creating images...')
        cre_ok, cre_fail = run_batches(api.image.create,
                                       [{'name': n, 'imagetype': want_type, 'image': b64(n)} for n in to_create],
                                       args.batch, {})

        failed = upd_fail + cre_fail
        print('Done: %d replaced, %d created, %d failed' % (upd_ok, cre_ok, len(failed)))
        for name, err in failed:
            print('  FAILED %s: %s' % (name, err))
        if any('permission' in err.lower() for _, err in failed):
            print('The API user must be a Super admin to create or update images.')
        return 1 if failed else 0
    except API_ERRORS as e:
        print('Error: %s' % e, file=sys.stderr)
        return 2
    finally:
        try:
            api.logout()
        except API_ERRORS:
            pass


if __name__ == '__main__':
    sys.exit(main())
