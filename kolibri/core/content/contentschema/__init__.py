"""
This is a dummy Django app for the entire purpose of generating content
schemas for import operations. This should not be enabled in production.

Each version's schema is also frozen here as data, so that reading one needs
neither this app to be installed nor a database to reflect: a table to column
map under `columns/`, and a SQLite DDL dump under `schema_ddl/`. Both are
written by the `generate_schema` management command, off the schema Django has
just migrated.
"""

import os

default_app_config = "kolibri.core.content.contentschema.apps.ContentSchemaConfig"


def schema_ddl_path(version):
    return os.path.join(os.path.dirname(__file__), "schema_ddl", version + ".sql")
