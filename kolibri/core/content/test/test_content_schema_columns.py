from django.apps import apps
from django.test import TestCase

from kolibri.core.content.constants.schema_versions import CONTENT_SCHEMA_VERSION
from kolibri.core.content.constants.schema_versions import CURRENT_SCHEMA_VERSION
from kolibri.core.content.constants.schema_versions import EXPORT_SCHEMA_VERSIONS
from kolibri.core.content.contentschema.columns import for_version


class ForVersionTestCase(TestCase):
    def test_a_version_with_no_frozen_map_raises(self):
        # CURRENT_SCHEMA_VERSION is not an exported version, so it has no frozen map.
        for version in (str(int(CONTENT_SCHEMA_VERSION) + 1), CURRENT_SCHEMA_VERSION):
            with self.subTest(version=version):
                with self.assertRaises(ValueError):
                    for_version(version)

    def test_export_columns_resolve_against_the_current_models(self):
        by_table = {
            model._meta.db_table: model
            for model in apps.get_app_config("content").get_models(
                include_auto_created=True
            )
        }
        for version in EXPORT_SCHEMA_VERSIONS:
            for table, columns in for_version(version).items():
                with self.subTest(version=version, table=table):
                    self.assertIn(table, by_table)
                    # An exported column may be either a current field's column or
                    # its attname — LocalFile.file_size is stored as file_size_bigint.
                    names = {
                        name
                        for field in by_table[table]._meta.concrete_fields
                        for name in (field.column, field.attname)
                    }
                    self.assertEqual(set(), set(columns) - names)
