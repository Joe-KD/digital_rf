# ----------------------------------------------------------------------------
# Copyright (c) 2017 Massachusetts Institute of Technology (MIT)
# All rights reserved.
#
# Distributed under the terms of the BSD 3-clause license.
#
# The full license is in the LICENSE file, distributed with this software.
# ----------------------------------------------------------------------------
"""Module for listing Digital RF/Metadata files in a directory."""
import os
import re

from six.moves import zip

__all__ = (
    'GLOB_DMDFILE', 'GLOB_DMDPROPFILE', 'GLOB_DRFFILE', 'GLOB_DRFPROPFILE',
    'GLOB_SUBDIR', 'RE_DMD', 'RE_DMDPROP', 'RE_DRF', 'RE_DRFDMD',
    'RE_DRFDMDPROP', 'RE_DRFPROP',
    'ilsdrf', 'lsdrf', 'sortkey_drf'
)

# timestamped subdirectory, e.g. 2016-09-21T20-00-00
GLOB_SUBDIR = (
    '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
    'T[0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
)
RE_SUBDIR = (
    r'(?P<ymd>[0-9]{4}-[0-9]{2}-[0-9]{2})'
    r'T(?P<hms>[0-9]{2}-[0-9]{2}-[0-9]{2})'
)

# Digital RF file, e.g. rf@1474491360.000.h5
GLOB_DRFFILE = '*@[0-9]*.[0-9][0-9][0-9].h5'
RE_DRFFILE = r'(?P<name>(?!tmp\.).+?)@(?P<secs>[0-9]+)\.(?P<frac>[0-9]{3})\.h5'

# Digital Metadata file, e.g. metadata@1474491360.h5
GLOB_DMDFILE = '*@[0-9]*.h5'
RE_DMDFILE = r'(?P<name>(?!tmp\.).+?)@(?P<secs>[0-9]+)\.h5'

# either Digital RF or Digital Metadata file
RE_FILE = (
    r'(?P<name>(?!tmp\.).+?)@(?P<secs>[0-9]+)(?:\.(?P<frac>[0-9]{3}))?\.h5'
)

# Digital RF channel properties file, e.g. drf_properties.h5
# include pre-2.5-style metadata.h5 for now
GLOB_DRFPROPFILE = '*.h5'
RE_DRFPROPFILE = r'(?P<name>drf_properties|metadata)\.h5'

# Digital RF channel properties file, e.g. dmd_properties.h5
# include pre-2.5-style metadata.h5 for now
GLOB_DMDPROPFILE = '*.h5'
RE_DMDPROPFILE = r'(?P<name>dmd_properties|metadata)\.h5'

# either Digital RF or Digital Metadata channel properties file
RE_PROPFILE = r'(?P<name>(?:drf|dmd)_properties|metadata)\.h5'

# Digital RF file in correct subdirectory structure
RE_DRF = re.escape(os.sep).join((r'(?P<chpath>.*?)', RE_SUBDIR, RE_DRFFILE))
# Digital Metadata file in correct subdirectory structure
RE_DMD = re.escape(os.sep).join((r'(?P<chpath>.*?)', RE_SUBDIR, RE_DMDFILE))
# either Digital RF or Digital Metadata in its correct subdirectory
RE_DRFDMD = re.escape(os.sep).join((r'(?P<chpath>.*?)', RE_SUBDIR, RE_FILE))
# properties file associated with Digital RF directory
RE_DRFPROP = re.escape(os.sep).join((r'(?P<chpath>.*?)', RE_DRFPROPFILE))
# properties file associated with Digital Metadata directory
RE_DMDPROP = re.escape(os.sep).join((r'(?P<chpath>.*?)', RE_DMDPROPFILE))
# properties file associated with Digital RF or Digital Metadata directory
RE_DRFDMDPROP = re.escape(os.sep).join((r'(?P<chpath>.*?)', RE_PROPFILE))


def sortkey_drf(filename, regexes=[re.compile(RE_FILE)]):
    """Get key for a Digital RF filename to sort first by sample time."""
    matched = False
    for r in regexes:
        m = r.match(filename)
        if m:
            matched = True
            break
    try:
        secs = int(m.group('secs'))
    except (AttributeError, IndexError, TypeError):
        # no match, or regex matched but there is no 'secs' in regex
        secs = 0
    try:
        frac = int(m.group('frac'))
    except (AttributeError, IndexError, TypeError):
        # no match, or regex matched but there is no 'frac' in regex
        frac = 0
    try:
        name = m.group('name')
    except (AttributeError, IndexError, TypeError):
        # no match, or regex matched but there is no 'name' in regex
        name = filename
    key = (matched, secs*1000 + frac, name)
    return key


def ilsdrf(
    path, include_drf=True, include_dmd=True, include_drf_properties=None,
    include_dmd_properties=None,
):
    """Generator of Digital RF files recursively contained in a directory.

    Sub-directories will be traversed in alphabetical order and files from each
    directory will be yielded in Digital RF (time) order.


    Parameters
    ----------

    path : string
        Parent directory to list.

    include_drf : bool
        If True, include Digital RF files in listing.

    include_dmd : bool
        If True, include Digital Metadata files in listing.

    include_drf_properties : bool | None
        If True, include the Digital RF properties file in listing.
        If None, use `include_drf` value.

    include_dmd_properties : bool | None
        If True, include the Digital Metadata properties file in listing.
        If None, use `include_dmd` value.


    Yields
    ------

    Digital RF/Metadata files contained in `path`.

    """
    if include_drf_properties is None:
        include_drf_properties = include_drf
    if include_dmd_properties is None:
        include_dmd_properties = include_dmd

    regexes = []
    if include_drf and include_dmd:
        regexes.append(RE_DRFDMD)
    elif include_drf:
        regexes.append(RE_DRF)
    elif include_dmd:
        regexes.append(RE_DMD)
    if include_drf_properties and include_dmd_properties:
        regexes.append(RE_DRFDMDPROP)
    elif include_drf_properties:
        regexes.append(RE_DRFPROP)
    elif include_dmd_properties:
        regexes.append(RE_DMDPROP)

    regexes = [re.compile(r) for r in regexes]

    if os.path.isfile(path):
        if any(r.match(path) for r in regexes):
            yield path
    else:
        for root, dirs, files in os.walk(os.path.abspath(path)):
            # walk through directories in sorted order
            dirs.sort()
            # yield files from this directory in sorted order and filter all at
            # once so the regex only has to be evaluated once per file
            filepaths = [os.path.join(root, f) for f in files]
            keys = (sortkey_drf(f, regexes=regexes) for f in filepaths)
            decorated_files = [
                key[1:] + (f,) for key, f in zip(keys, filepaths) if key[0]
            ]
            decorated_files.sort()
            for decorated_file in decorated_files:
                yield decorated_file[-1]


def lsdrf(*args, **kwargs):
    """Get list of Digital RF files recursively contained in a directory.

    Parameters
    ----------

    path : string
        Parent directory to list.

    include_drf : bool
        If True, include Digital RF files in listing.

    include_dmd : bool
        If True, include Digital Metadata files in listing.

    include_drf_properties : bool | None
        If True, include the Digital RF properties file in listing.
        If None, use `include_drf` value.

    include_dmd_properties : bool | None
        If True, include the Digital Metadata properties file in listing.
        If None, use `include_dmd` value.


    Returns
    -------

    List of Digital RF/Metadata files contained in `path`.

    """
    return list(ilsdrf(*args, **kwargs))


def _build_ls_parser(Parser, *args):
    desc = 'List Digital RF files in a directory.'
    parser = Parser(*args, description=desc)

    parser.add_argument('dirs', nargs='*', default='.',
                        help='''Data directory to list.
                               (default: %(default)s)''')

    includegroup = parser.add_argument_group(title='include')
    includegroup.add_argument(
        '--nodrf', dest='include_drf', action='store_false',
        help='''Do not list Digital RF HDF5 files.
                (default: False)''',
    )
    includegroup.add_argument(
        '--nodmd', dest='include_dmd', action='store_false',
        help='''Do not list Digital Metadata HDF5 files.
                (default: False)''',
    )
    includegroup.add_argument(
        '--nodrfprops', dest='include_drf_properties', nargs='?',
        const=False, default=None,
        help='''Do not list drf_properties.h5 files.
                (default: Same as --nodrf)''',
    )
    includegroup.add_argument(
        '--nodmdprops', dest='include_dmd_properties', nargs='?',
        const=False, default=None,
        help='''Do not list dmd_properties.h5 files.
                (default: Same as --nodmd)''',
    )

    parser.set_defaults(func=_run_ls)

    return parser


def _run_ls(args):
    if args.include_drf_properties:
        args.include_drf_properties = True
    if args.include_dmd_properties:
        args.include_dmd_properties = True

    kwargs = vars(args).copy()
    del kwargs['func']
    del kwargs['dirs']

    files = []
    for d in args.dirs:
        files.extend(lsdrf(d, **kwargs))
    files.sort(key=sortkey_drf)
    print('\n'.join(files))


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = _build_ls_parser(ArgumentParser)
    args = parser.parse_args()
    args.func(args)
