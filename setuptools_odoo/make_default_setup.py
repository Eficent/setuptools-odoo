# -*- coding: utf-8 -*-
# © 2015 ACSONE SA/NV
# License LGPLv3 (http://www.gnu.org/licenses/lgpl-3.0-standalone.html)

import argparse
import os
import pprint
from distutils.core import DistutilsSetupError

from .core import (
    ADDONS_NAMESPACE,
    is_installable_addon,
    get_version,
    make_pkg_requirement,
)

SETUP_PY = """import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon=True,
)
"""

INIT_PY = """__import__('pkg_resources').declare_namespace(__name__)
"""

SETUP_PY_META = """import setuptools

install_requires = {install_requires}

setuptools.setup(
    name='{name}',
    version='{version}',
    install_requires=install_requires,
)
"""


def make_default_setup_addon(addon_setup_dir, addon_dir, force):
    addon_name = os.path.basename(os.path.realpath(addon_dir))
    setup_path = os.path.join(addon_setup_dir, 'setup.py')
    if not os.path.exists(setup_path) or force:
        with open(setup_path, 'w') as f:
            f.write(SETUP_PY.format(addon_name=addon_name))
    odoo_addons_path = os.path.join(addon_setup_dir, ADDONS_NAMESPACE)
    if not os.path.exists(odoo_addons_path):
        os.mkdir(odoo_addons_path)
    init_path = os.path.join(odoo_addons_path, '__init__.py')
    if not os.path.exists(init_path) or force:
        with open(init_path, 'w') as f:
            f.write(INIT_PY)
    link_path = os.path.join(odoo_addons_path, addon_name)
    # symlink to the main addon directory so we have a canonical structure:
    # odoo_addons/addon_name/...
    if os.path.exists(link_path) and force:
        os.remove(link_path)
    if not os.path.exists(link_path):
        os.symlink(os.path.relpath(addon_dir, odoo_addons_path), link_path)


def make_default_setup_addons_dir(addons_dir, force):
    addons_setup_dir = os.path.join(addons_dir, 'setup')
    if not os.path.exists(addons_setup_dir):
        os.mkdir(addons_setup_dir)
    for addon_name in os.listdir(addons_dir):
        addon_dir = os.path.join(addons_dir, addon_name)
        if not is_installable_addon(addon_dir):
            continue
        addon_setup_dir = os.path.join(addons_setup_dir, addon_name)
        if not os.path.exists(addon_setup_dir):
            os.mkdir(addon_setup_dir)
        make_default_setup_addon(addon_setup_dir, addon_dir, force)


def make_default_meta_package_setup(addons_dir, meta_package_setup):
    addons_dir = os.path.abspath(addons_dir)
    meta_install_requires = []
    odoo_versions = set()
    for addon_name in os.listdir(addons_dir):
        addon_dir = os.path.join(addons_dir, addon_name)
        if not is_installable_addon(addon_dir):
            continue
        meta_install_requires.append(make_pkg_requirement(addon_dir))
        _, odoo_version, _ = get_version(addon_dir)
        odoo_versions.add(odoo_version)
    if len(odoo_versions) == 0:
        # no addon found
        return
    if len(odoo_versions) > 1:
        raise DistutilsSetupError("not all addon are for the same "
                                  "Odoo version: %s" % (odoo_versions,))
    meta_install_requires = pprint.pformat(sorted(meta_install_requires),
                                           indent=4, width=50)
    setup_py = SETUP_PY_META.format(name=os.path.basename(addons_dir),
                                    version=list(odoo_versions)[0],
                                    install_requires=meta_install_requires)
    open(meta_package_setup, 'w').write(setup_py)


def main(args=None):
    parser = argparse.ArgumentParser(
        description='Generate default setup.py for all addons in an '
                    'Odoo addons directory'
    )
    parser.add_argument('--addons-dir', '-d', required=True)
    parser.add_argument('--force', '-f', action='store_true')
    parser.add_argument('--meta-package-setup', '-m')
    args = parser.parse_args(args)
    make_default_setup_addons_dir(args.addons_dir, args.force)
    if args.meta_package_setup:
        if args.force or not os.path.exists(args.meta_package_setup):
            make_default_meta_package_setup(args.addons_dir,
                                            args.meta_package_setup)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
