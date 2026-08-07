"""
Read-only introspection of a channel database file.

Channel databases are SQLite files exported by Studio at one of the historical
content schema versions.
"""

import sqlite3
from pathlib import Path

from django.utils.functional import cached_property

from kolibri.core.content.contentschema.columns import version_for_shape
from kolibri.core.content.errors import SchemaNotFoundError


class SourceDB:
    """
    An absent or unreadable file raises `sqlite3.OperationalError` from the
    constructor; a corrupt one opens cleanly and raises `sqlite3.DatabaseError` on
    the first query instead.
    """

    def __init__(self, path):
        self.path = path
        self._connection = sqlite3.connect(
            "{}?mode=ro".format(Path(path).absolute().as_uri()), uri=True
        )
        self._connection.row_factory = sqlite3.Row

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self._connection.close()

    @cached_property
    def _shape(self):
        """
        Every table in this file mapped to its column names, in declaration order.
        """
        names = [
            row["name"]
            for row in self._connection.execute(
                # An AUTOINCREMENT primary key gives the file a sqlite_sequence
                # table, which is bookkeeping rather than schema.
                "SELECT name FROM sqlite_master"
                " WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        ]
        return {
            name: [
                row["name"]
                for row in self._connection.execute(
                    'PRAGMA table_info("{}")'.format(name)
                )
            ]
            for name in names
        }

    def tables(self):
        return set(self._shape)

    def columns(self, table):
        """
        The table's column names in declaration order, or an empty list if the
        table is not in this file.
        """
        return self._shape.get(table, [])

    def rows(self, table):
        if table not in self._shape:
            raise ValueError("No table named {} in {}".format(table, self.path))
        return [
            dict(row)
            for row in self._connection.execute('SELECT * FROM "{}"'.format(table))
        ]

    @cached_property
    def schema_version(self):
        version = version_for_shape(self._shape)
        if version is None:
            raise SchemaNotFoundError(
                "No matching schema found for database {}".format(self.path)
            )
        return version
