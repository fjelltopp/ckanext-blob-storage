"""Tests for plugin.py."""
# encoding: utf-8
from ckan.plugins import toolkit
from ckan.tests import factories
import pytest
import logging
from ckanext.unaids.tests import get_context
import mock


log = logging.getLogger(__name__)


@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestBlobStorageActivityDownload(object):
    def test_can_download_release_resource_whether_it_exists_in_current_version_of_package_or_not(self, app):
        org_admin = factories.User()

        org = factories.Organization(user=org_admin)
        context = get_context(org_admin)

        dataset = factories.Dataset(owner_org=org['id'])
        resource = toolkit.get_action('resource_create')(
            context,
            {
                "name": 'Test',
                "description": "Test resource",
                "url_type": "upload",
                "lfs_prefix": "test/prefix",
                "filename": "test.csv",
                "sha256": "acbac3b78f9ace071ca3a79f23fc788a1b7ee9dc547becc6404dbb1f58afff79",
                "size": 50,
                "package_id": dataset["id"]
            }
        )

        # Download the resource from activity
        with mock.patch('ckanext.blob_storage.blueprints.call_download_handlers') as m:
            m.return_value = ''
            url = toolkit.url_for(
                'blob_storage.download',
                id=dataset['id'],
                resource_id=resource['id'],
                filename="test.csv",
            )
            app.get(url, status=200)

        # Now delete the resource
        toolkit.get_action('resource_delete')(context, {'id': resource['id']})

        # Check is the resource exists
        with mock.patch('ckanext.blob_storage.blueprints.call_download_handlers') as m:
            m.return_value = ''
            url = toolkit.url_for(
                'blob_storage.download',
                id=dataset['id'],
                resource_id=resource['id'],
                filename="test.csv",
            )
            app.get(url, status=404)

        # Let's get the id of second activity stream
        activity_list = toolkit.get_action('package_activity_list')(context, {'id': dataset['id'], 'include_hidden_activity': True})
        # Will give 3 activities
        # activity_list[0] : resource deleted
        # activity_list[1]: we added the resource
        # activity_list[2]: we created the package
        version = activity_list[1]

        # Check if we can download the resource from the version
        with mock.patch('ckanext.blob_storage.blueprints.call_download_handlers') as m:
            m.return_value = ''
            url = toolkit.url_for(
                'blob_storage.download',
                id=dataset['id'],
                resource_id=resource['id'],
                activity_id=version['id'],
                filename="test.csv",
                preview=1
            )

            app.get(url, status=200, extra_environ={'REMOTE_USER': org_admin['name']})




