"""Tests for plugin.py
"""
import ckanext.blob_storage.plugin as plugin


def test_plugin():
    p = plugin.BlobStoragePlugin()
    assert p
