"""
Writable access to a content database file through a Django database alias
registered for the lifetime of a `content_db` block.
"""

import re
import uuid
from contextlib import contextmanager

from django.conf import settings
from django.db import connections
from django.db import DEFAULT_DB_ALIAS

from kolibri.core.content.models import AssessmentMetaData
from kolibri.core.content.models import ChannelMetadata
from kolibri.core.content.models import ContentNode
from kolibri.core.content.models import ContentTag
from kolibri.core.content.models import File
from kolibri.core.content.models import Language
from kolibri.core.content.models import LocalFile

CONTENT_DB_ALIAS_PREFIX = "content_"

# The concrete content models, in an order that satisfies their foreign keys. The
# schema editor creates each model's own many to many through tables, so those must
# not be listed here as well.
_SCHEMA_MODELS = (
    Language,
    ContentTag,
    LocalFile,
    ContentNode,
    File,
    AssessmentMetaData,
    ChannelMetadata,
)

# \Z rather than $, which would also match a name ending in a newline.
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


@contextmanager
def content_db(path=None):
    """
    Yield a Django database alias for the content database at path, deregistered
    and closed when the block exits. A path of None yields the default alias
    instead, registering nothing.
    """
    if path is None:
        yield DEFAULT_DB_ALIAS
        return
    alias = CONTENT_DB_ALIAS_PREFIX + uuid.uuid4().hex
    settings.DATABASES[alias] = {
        # Content databases are sqlite files whatever the default database is.
        "ENGINE": "kolibri.deployment.default.db.backends.sqlite3",
        "NAME": path,
        # Content import writes should wait out lock contention rather than fail.
        "OPTIONS": {"timeout": 5 * 60},
    }
    try:
        yield alias
    finally:
        # Touch the connection first, as deleting one never created raises.
        # Deregister before closing, so a failing close cannot leave the alias behind.
        connection = connections[alias]
        del connections[alias]
        del settings.DATABASES[alias]
        connection.close()


def create_schema(alias):
    connection = connections[alias]
    existing = set(connection.introspection.table_names())
    missing = [
        model for model in _SCHEMA_MODELS if model._meta.db_table not in existing
    ]
    # Leaving the schema editor takes a whole database PRAGMA foreign_key_check, so
    # do not enter it at all when there is nothing to create.
    if not missing:
        return
    with connection.schema_editor() as editor:
        for model in missing:
            editor.create_model(model)


@contextmanager
def attached_database(alias, path, name):
    if not _IDENTIFIER.match(name):
        raise ValueError("Invalid attached database name: {}".format(name))
    with connections[alias].cursor() as cursor:
        # The schema name cannot be bound as a parameter, so _IDENTIFIER guards
        # inlining it.
        cursor.execute("ATTACH DATABASE %s AS " + name, [path])
    try:
        yield
    finally:
        with connections[alias].cursor() as cursor:
            cursor.execute("DETACH DATABASE " + name)
