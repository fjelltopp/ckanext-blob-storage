"""Regression tests: downloads must be served by blob_storage's own view.

Background
----------
CKAN registers its own download routes with a fixed prefix for every package
type, e.g. ``/dataset/<id>/resource/<resource_id>/download`` and
``/dataset-2/<id>/resource/...``. A single ``/<package_type>/...`` wildcard
route loses against those (Werkzeug prefers routes with more fixed text), so
blob_storage registers one fixed-prefix route per package type instead. Its
view understands ``?activity_id=`` and ``?preview=``; CKAN core's view does not.
"""
import pytest
from unittest import mock

from ckan.lib import plugins as lib_plugins
from ckan.plugins import toolkit
from ckan.tests import factories, helpers
from giftless_client import LfsClient


SHA_OLD = 'a' * 64
SHA_NEW = 'b' * 64
LFS_PREFIX = 'test-org/test-dataset'


def _registered_package_types():
    # 'dataset' is always routable, even when no plugin claims it explicitly.
    return sorted(set(lib_plugins._package_plugins) | {'dataset'})


# --------------------------------------------------------------------------
# 1. Routing: which view answers a download URL?
# --------------------------------------------------------------------------

class TestDownloadRouting(object):

    @pytest.mark.usefixtures('with_plugins')
    @pytest.mark.parametrize('suffix', ['', '/data.csv'])
    @pytest.mark.parametrize('package_type', _registered_package_types())
    def test_download_url_is_served_by_blob_storage_view(self, app, package_type, suffix):
        """Every registered package type must reach blob_storage.download.

        If CKAN core's `<package_type>_resource.download` wins, ?activity_id= is ignored.
        """
        path = '/{}/some-dataset/resource/some-resource/download{}'.format(package_type, suffix)
        adapter = app.flask_app.url_map.bind('localhost')

        endpoint, _ = adapter.match(path)

        assert endpoint == 'blob_storage.download', (
            '{} is served by {!r}, not by blob_storage. ?activity_id= and '
            '?preview= are ignored on this URL.'.format(path, endpoint)
        )


# --------------------------------------------------------------------------
# 2. End to end: ?activity_id= must download the historic file
# --------------------------------------------------------------------------

def _fake_lfs_batch(prefix, operation, objects):
    """Stand-in for the Giftless batch API: echo each oid back in a URL."""
    return {
        'objects': [
            {
                'oid': obj['oid'],
                'size': obj['size'],
                'actions': {'download': {'href': 'https://storage.test/{}/{}'.format(prefix, obj['oid'])}},
            }
            for obj in objects
        ]
    }


def _activity_with_sha(dataset_id, resource_id, sha256):
    """Find the activity in which the resource had the given sha256."""
    for activity in helpers.call_action('package_activity_list', id=dataset_id, include_hidden_activity=True):
        full = helpers.call_action('activity_show', id=activity['id'], include_data=True)
        for res in full['data']['package']['resources']:
            if res['id'] == resource_id and res.get('sha256') == sha256:
                return activity['id']
    pytest.fail('Test setup: no activity found where the resource has sha256 {}'.format(sha256))


@pytest.mark.usefixtures('clean_db_with_migrations', 'with_plugins')
class TestActivityDownload(object):

    @pytest.fixture
    def versioned_resource(self):
        """A resource uploaded twice, so its history has two different files."""
        user = factories.Sysadmin()
        context = {'user': user['name']}
        org = factories.Organization()
        dataset = helpers.call_action(
            'package_create', context=dict(context), name='versioned-dataset', owner_org=org['id']
        )
        resource = helpers.call_action(
            'resource_create', context=dict(context),
            package_id=dataset['id'], name='data.csv', url='data.csv', url_type='upload',
            sha256=SHA_OLD, size=10, lfs_prefix=LFS_PREFIX,
        )
        helpers.call_action(
            'resource_patch', context=dict(context),
            id=resource['id'], sha256=SHA_NEW, size=20,
        )
        return {
            'user': user,
            'dataset': dataset,
            'resource': resource,
            'old_activity_id': _activity_with_sha(dataset['id'], resource['id'], SHA_OLD),
        }

    def _download(self, app, fixture, **query):
        url = toolkit.url_for(
            'blob_storage.download', package_type='dataset',
            id=fixture['dataset']['id'], resource_id=fixture['resource']['id'],
            filename='data.csv', **query
        )
        with mock.patch.object(LfsClient, 'batch', side_effect=_fake_lfs_batch) as batch:
            response = app.get(
                url, status=302, follow_redirects=False,
                extra_environ={'REMOTE_USER': fixture['user']['name']},
            )
        return response, batch

    def test_without_activity_id_downloads_current_file(self, app, versioned_resource):
        """Control: this already works, so a failure elsewhere is a real signal."""
        response, _ = self._download(app, versioned_resource)

        assert SHA_NEW in response.headers['Location']

    def test_activity_id_downloads_historic_file(self, app, versioned_resource):
        """The bug: ?activity_id=<id> returns the latest file instead."""
        response, _ = self._download(
            app, versioned_resource, activity_id=versioned_resource['old_activity_id']
        )

        location = response.headers['Location']
        assert SHA_OLD in location, 'Expected the historic file, redirected to {}'.format(location)
        assert SHA_NEW not in location

    def test_preview_requests_inline_disposition(self, app, versioned_resource):
        """?preview=1 must ask the storage server for an inline response."""
        _, batch = self._download(app, versioned_resource, preview=1)

        requested_objects = batch.call_args[0][2]
        assert requested_objects[0].get('x-disposition') == 'inline'
