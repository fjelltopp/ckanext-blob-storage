"""Tests for the DummyUploader."""
import pytest

from ckanext.blob_storage.uploader import DummyUploader


class TestDummyUploader:

    def test_init_stores_resource(self):
        resource = {'id': 'res-123', 'package_id': 'pkg-456', 'name': 'data.csv'}

        assert DummyUploader(resource).resource == resource

    def test_get_path_raises_a_clear_error(self):
        """Blob-storage files have no local path; reaching CKAN core's download
        view for them is a routing bug and must not be papered over."""
        uploader = DummyUploader({'id': 'res-123', 'package_id': 'pkg-456'})

        with pytest.raises(NotImplementedError, match='res-123'):
            uploader.get_path('res-123')

    def test_upload_returns_none(self):
        uploader = DummyUploader({'id': 'res-123', 'package_id': 'pkg-456'})

        assert uploader.upload('res-123', max_size=1000) is None
