"""Tests for plugin.py."""
# encoding: utf-8
from ckan.plugins import toolkit
from ckan.tests.helpers import call_action
from ckan.tests import factories
import pytest
import logging
from ckanext.auth import logic
from ckanext.unaids.tests import get_context
import mock
import ckan.logic as logic

log = logging.getLogger(__name__)


@pytest.mark.ckan_config('ckan.plugins', 'unaids versions blob_storage authz_service pages')
@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestBlobStorageActivityDownload(object):
    def test_can_download_resource_whether_it_exist_in_current_version_of_package_or_not(self, app, org_admin):

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
        # Now, create the activity
        version = toolkit.get_action('dataset_version_create')(
            context,
            {
                "dataset_id": dataset['id'],
                "name": "V1.0"
            }
        )
        # check if release exists
        dataset = call_action('package_show',
                              context,
                              id=dataset['id'],
                              release=version['name']
                              )

        assert 'activity_id={}'.format(version['activity_id']) in dataset['resources'][0]['url']

        # Download the resource
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
        with pytest.raises(logic.NotFound):
            toolkit.get_action('resource_show')(context, {'id': resource['id'], 'activity_id': version['activity_id']})

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

        # Check if we can download the resource from the version
        with mock.patch('ckanext.blob_storage.blueprints.call_download_handlers') as m:
            m.return_value = ''
            url = toolkit.url_for(
                'blob_storage.download',
                id=dataset['id'],
                resource_id=resource['id'],
                activity_id=version['activity_id'],
                filename="test.csv",
                preview=1
            )

            app.get(url, status=200, extra_environ={'REMOTE_USER': org_admin['name']})


