import pytest
from django.conf import settings

from kolibri.core.content.utils.content_db import CONTENT_DB_ALIAS_PREFIX


@pytest.fixture(autouse=True)
def no_leaked_content_db_aliases():
    """
    An alias outliving a test means some content_db() block skipped its exit path,
    leaving an open connection behind.
    """
    yield
    leaked = [
        alias
        for alias in settings.DATABASES
        if alias.startswith(CONTENT_DB_ALIAS_PREFIX)
    ]
    assert not leaked, "Content database aliases were left registered: {}".format(
        ", ".join(leaked)
    )
