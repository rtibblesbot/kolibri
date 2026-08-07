"""
Frozen table to column maps, one module per content schema version.
"""

import importlib
import os
from functools import lru_cache

from kolibri.core.content.constants.schema_versions import (
    coerce_version_name_to_valid_module_path,
)
from kolibri.core.content.constants.schema_versions import CONTENT_DB_SCHEMA_VERSIONS


def _module_name(version):
    return "content_columns_" + coerce_version_name_to_valid_module_path(version)


def module_path(version):
    return os.path.join(os.path.dirname(__file__), _module_name(version) + ".py")


def for_version(version):
    """
    A content schema version's table names mapped to its column names, in
    declaration order.
    """
    if version not in CONTENT_DB_SCHEMA_VERSIONS:
        raise ValueError("Unknown content schema version {}".format(version))
    return importlib.import_module("." + _module_name(version), __name__).COLUMNS


@lru_cache(maxsize=None)
def _versions_by_specificity():
    # Schema 3 dropped ContentNode.stemmed_metaphone and File.available, so every
    # version 2 database also satisfies version 3. Ordering by declared column
    # count tries the container first.
    return sorted(
        CONTENT_DB_SCHEMA_VERSIONS,
        key=lambda version: (
            -sum(len(columns) for columns in for_version(version).values())
        ),
    )


def version_for_shape(shape):
    """
    The most specific version `shape` satisfies, or None if it satisfies none.

    `shape` maps table name to column names, as a database file declares them. A
    file may declare more than its own version does, as a Studio export does, so
    this matches on superset rather than equality.
    """
    declared = {table: frozenset(columns) for table, columns in shape.items()}
    for version in _versions_by_specificity():
        if all(
            declared.get(table, frozenset()).issuperset(columns)
            for table, columns in for_version(version).items()
        ):
            return version
    return None
