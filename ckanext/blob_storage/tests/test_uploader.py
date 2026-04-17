"""Tests for the DummyUploader and BlobStorageRedirectException.

These tests verify that when CKAN 2.11's core download route is called
for blob-storage resources, the uploader correctly redirects to the
blob-storage download endpoint.
"""
import pytest
from unittest import mock

from ckanext.blob_storage.uploader import (
    DummyUploader,
    BlobStorageRedirectException
)


class TestBlobStorageRedirectException:
    """Tests for the redirect exception."""

    def test_exception_stores_resource_info(self):
        """Exception should store resource_id, package_id, and filename."""
        exc = BlobStorageRedirectException(
            resource_id='res-123',
            package_id='pkg-456',
            filename='data.csv'
        )

        assert exc.resource_id == 'res-123'
        assert exc.package_id == 'pkg-456'
        assert exc.filename == 'data.csv'

    def test_exception_without_filename(self):
        """Exception should work without a filename."""
        exc = BlobStorageRedirectException(
            resource_id='res-123',
            package_id='pkg-456'
        )

        assert exc.resource_id == 'res-123'
        assert exc.package_id == 'pkg-456'
        assert exc.filename is None

    @mock.patch('giftless_client.LfsClient')
    @mock.patch('ckanext.blob_storage.actions.get_download_authz_token')
    @mock.patch('ckanext.blob_storage.helpers.server_url')
    @mock.patch('ckanext.blob_storage.helpers.resource_filename')
    @mock.patch('ckan.plugins.toolkit.get_action')
    @mock.patch('flask.redirect')
    @mock.patch('flask_login.current_user', name='test-user', new_callable=mock.MagicMock)
    def test_get_response_creates_redirect(
        self, mock_current_user, mock_redirect, mock_get_action, mock_resource_filename,
        mock_server_url, mock_get_authz_token, mock_lfs_client_class
    ):
        """get_response() should fetch LFS URL and redirect to blob storage."""
        # Setup mocks
        mock_resource = {
            'id': 'res-123',
            'sha256': 'abc123',
            'size': 1000,
            'lfs_prefix': 'org/dataset'
        }
        mock_package = {
            'id': 'pkg-456',
            'name': 'my-dataset',
            'organization': {'name': 'my-org'}
        }

        def mock_action(action_name):
            def action_fn(context, data):
                if action_name == 'resource_show':
                    return mock_resource
                elif action_name == 'package_show':
                    return mock_package
            return action_fn

        mock_get_action.side_effect = mock_action
        mock_get_authz_token.return_value = 'auth-token-xyz'
        mock_server_url.return_value = 'https://lfs.example.com'
        mock_resource_filename.return_value = 'data.csv'

        # Setup LFS client mock
        mock_lfs_client = mock.MagicMock()
        mock_lfs_client_class.return_value = mock_lfs_client
        mock_lfs_client.batch.return_value = {
            'objects': [{
                'actions': {
                    'download': {'href': 'https://blob.storage.azure.net/file?sas=token'}
                }
            }]
        }

        mock_redirect.return_value = 'redirect_response'

        exc = BlobStorageRedirectException(
            resource_id='res-123',
            package_id='pkg-456',
            filename='data.csv'
        )

        response = exc.get_response()

        # Verify LFS client was created with correct server and token
        mock_lfs_client_class.assert_called_once_with(
            'https://lfs.example.com', 'auth-token-xyz'
        )

        # Verify redirect was called with the LFS download URL
        mock_redirect.assert_called_once_with(
            'https://blob.storage.azure.net/file?sas=token'
        )

        assert response == 'redirect_response'


class TestDummyUploader:
    """Tests for the DummyUploader class."""

    def test_init_stores_resource(self):
        """Uploader should store the resource dict."""
        resource = {'id': 'res-123', 'package_id': 'pkg-456', 'name': 'data.csv'}
        uploader = DummyUploader(resource)

        assert uploader.resource == resource

    def test_get_path_raises_redirect_exception(self):
        """get_path() should raise BlobStorageRedirectException."""
        resource = {
            'id': 'res-123',
            'package_id': 'pkg-456',
            'name': 'my-data.csv'
        }
        uploader = DummyUploader(resource)

        with pytest.raises(BlobStorageRedirectException) as exc_info:
            uploader.get_path('res-123')

        exc = exc_info.value
        assert exc.resource_id == 'res-123'
        assert exc.package_id == 'pkg-456'
        assert exc.filename == 'my-data.csv'

    def test_get_path_without_package_id_returns_none(self):
        """get_path() should return None if package_id is missing."""
        resource = {'id': 'res-123', 'name': 'data.csv'}
        uploader = DummyUploader(resource)

        # Without package_id, we can't build a redirect URL
        result = uploader.get_path('res-123')
        assert result is None

    def test_upload_returns_none(self):
        """upload() should return None (no-op for blob-storage)."""
        resource = {'id': 'res-123', 'package_id': 'pkg-456'}
        uploader = DummyUploader(resource)

        result = uploader.upload('res-123', max_size=1000)
        assert result is None


class TestDummyUploaderIntegration:
    """Integration-style tests simulating CKAN's download flow."""

    def test_ckan_download_flow_triggers_redirect(self):
        """
        Simulate what happens when CKAN core's download view calls get_path().

        In CKAN 2.11, the download view does:
            upload = uploader.get_resource_uploader(rsc)
            filepath = upload.get_path(rsc['id'])
            resp = flask.send_file(filepath, ...)

        With our fix, get_path() raises an exception that Flask catches
        and converts to a redirect response.
        """
        resource = {
            'id': 'resource-abc-123',
            'package_id': 'dataset-xyz-789',
            'name': 'important-data.xlsx',
            'url_type': 'upload',
            'lfs_prefix': 'org/dataset-xyz-789'
        }

        uploader = DummyUploader(resource)

        # This simulates CKAN calling get_path()
        with pytest.raises(BlobStorageRedirectException) as exc_info:
            uploader.get_path(resource['id'])

        # The exception contains the info needed for the redirect
        exc = exc_info.value
        assert exc.resource_id == 'resource-abc-123'
        assert exc.package_id == 'dataset-xyz-789'
        assert exc.filename == 'important-data.xlsx'

    def test_uploader_preserves_resource_metadata(self):
        """Uploader should preserve all resource metadata for the redirect."""
        resource = {
            'id': 'res-123',
            'package_id': 'pkg-456',
            'name': 'data with spaces.csv',
            'format': 'CSV',
            'mimetype': 'text/csv',
            'size': 12345,
            'sha256': 'abc123...',
            'lfs_prefix': 'myorg/mypkg'
        }

        uploader = DummyUploader(resource)

        # All resource data should be accessible
        assert uploader.resource['format'] == 'CSV'
        assert uploader.resource['size'] == 12345
        assert uploader.resource['lfs_prefix'] == 'myorg/mypkg'
