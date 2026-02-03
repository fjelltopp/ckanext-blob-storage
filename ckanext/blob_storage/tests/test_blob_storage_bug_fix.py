import logging
import mock
import pytest

from ckan.plugins import toolkit
from ckan.tests import factories, helpers

log = logging.getLogger(__name__)


# In CKAN 2.11+, the core /dataset/.../download route takes precedence over
# blob_storage's /<package_type>/.../download route due to Flask preferring
# literal path segments over variables. The blob_storage download functionality
# is instead provided via DummyUploader.get_path() raising BlobStorageRedirectException.
@pytest.mark.skipif(
    toolkit.check_ckan_version(min_version='2.11'),
    reason="CKAN 2.11+ uses uploader mechanism instead of blob_storage route for /dataset/ URLs"
)
@pytest.mark.usefixtures('clean_db_with_migrations', 'with_plugins')
class TestBlobStorageActivityDownload(object):
    def test_can_download_release_resource_whether_it_exists_in_current_version_of_package_or_not(self, app):
        user = factories.User()
        dataset = helpers.call_action('package_create', context={'user': user['name']}, name='dataset_for_bug_test')
        resource = helpers.call_action('resource_create', context={'user': user['name']}, package_id=dataset["id"])

        helpers.call_action('resource_delete', context={'user': user['name']}, id=resource['id'])

        activity_list = helpers.call_action('package_activity_list', id=dataset['id'], include_hidden_activity=True)
        activity_before_deleted_resource = activity_list[1]

        with mock.patch('ckanext.blob_storage.blueprints.call_download_handlers', return_value=''):
            url = toolkit.url_for(
                'blob_storage.download',
                package_type='dataset',
                id=dataset['id'],
                resource_id=resource['id'],
                activity_id=activity_before_deleted_resource['id'],
                filename="test.csv",
                preview=1
            )
            # REMOTE_USER is needed to access the resource since resources from old activities are not public
            app.get(url, status=200, extra_environ={'REMOTE_USER': user['name']})
