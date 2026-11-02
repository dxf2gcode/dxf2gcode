"""Version mappings for Python packages and the three-field MSI format."""

import re


def release_base(version):
    match = re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:\.dev\d+)?', version)
    if not match:
        raise ValueError('Expected MAJOR.MINOR.PATCH, optionally followed by .devN')
    return '.'.join(match.groups())


def msi_version(version, build_number=None):
    major, minor, patch = map(int, release_base(version).split('.'))
    if '.dev' in version:
        patch = int(build_number if build_number is not None else version.split('.dev')[1])
    if not (0 <= major <= 255 and 0 <= minor <= 255 and 0 <= patch <= 65535):
        raise ValueError('MSI version exceeds 255.255.65535; never wrap build numbers')
    return '%d.%d.%d' % (major, minor, patch)
