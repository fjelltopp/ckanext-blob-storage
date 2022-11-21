"""Tests for plugin.py."""
# encoding: utf-8
from ckan.plugins import toolkit
from ckan.tests import factories, helpers
import pytest
import logging
from ckanext.unaids.tests import get_context
import mock


log = logging.getLogger(__name__)


@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestBlobStorageActivityDownload(object):
    def test_can_download_release_resource_whether_it_exists_in_current_version_of_package_or_not(self, app):

        user = factories.User()
        dataset = helpers.call_action('package_create', name='dataset_for_bug_test')
        resource = helpers.call_action('resource_create', package_id=dataset["id"])

        # Now delete the resource
        helpers.call_action('resource_delete', id=resource['id'])

        # Let's get the id of second activity stream
        activity_list = helpers.call_action('package_activity_list', id=dataset['id'], include_hidden_activity=True)
        activity_before_deleted_resource = activity_list[1]

        # # Check if we can download the resource from the version
        with mock.patch('ckanext.blob_storage.blueprints.call_download_handlers', return_value=''):
            url = toolkit.url_for(
                'blob_storage.download',
                id=dataset['id'],
                resource_id=resource['id'],
                activity_id=activity_before_deleted_resource['id'],
                filename="test.csv",
                preview=1
            )
            # REMOTE_USER is needed to access the resource since resources from old activities are not public
            app.get(url, status=200, extra_environ={'REMOTE_USER': user['name']})




