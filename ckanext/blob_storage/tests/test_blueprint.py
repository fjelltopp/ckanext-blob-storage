import mock
import pytest
from ckan.plugins import toolkit
from ckan.tests import factories


# In CKAN 2.11+, the core /dataset/.../download route takes precedence over
# blob_storage's /<package_type>/.../download route due to Flask preferring
# literal path segments over variables. The blob_storage download functionality
# is instead provided via DummyUploader.get_path() raising BlobStorageRedirectException.
@pytest.mark.skipif(
    toolkit.check_ckan_version(min_version='2.11'),
    reason="CKAN 2.11+ uses uploader mechanism instead of blob_storage route for /dataset/ URLs"
)
@pytest.mark.usefixtures('clean_db')
def test_preview_arg(app):

    org = factories.Organization()
    dataset = factories.Dataset(owner_org=org['id'])
    resource = factories.Resource(
        package_id=dataset['id'],
        url_type='upload',
        sha256='cc71500070cf26cd6e8eab7c9eec3a937be957d144f445ad24003157e2bd0919',
        size=12,
        lfs_prefix='lfs/prefix'
    )

    with mock.patch('ckanext.blob_storage.blueprints.call_download_handlers') as m:

        m.return_value = ''

        url = toolkit.url_for(
            'blob_storage.download',
            package_type='dataset',
            id=dataset['id'],
            resource_id=resource['id'],
            preview=1
        )

        app.get(url)

        args = m.call_args

        assert args[0][0]['id'] == resource['id']   # resource
        assert args[0][1]['id'] == dataset['id']    # dataset
        assert args[0][2] is None                   # filename
        assert args[0][3] is True                   # inline

        url = toolkit.url_for(
            'blob_storage.download',
            package_type='dataset',
            id=dataset['id'],
            resource_id=resource['id'],
            filename='test.csv',
            preview=1
        )

        app.get(url)

        args = m.call_args

        assert args[0][2] == 'test.csv'             # filename
        assert args[0][3] is True                   # inline

        url = toolkit.url_for(
            'blob_storage.download',
            package_type='dataset',
            id=dataset['id'],
            resource_id=resource['id'],
            filename='test.csv',
        )

        app.get(url)

        args = m.call_args

        assert args[0][3] is False                   # inline
