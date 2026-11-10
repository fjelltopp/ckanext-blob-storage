"""Tests for the resource download handler plumbing."""
from unittest import mock

from ckanext.blob_storage.download_handler import call_pre_download_handlers


def test_pre_download_handlers_receive_the_activity_id():
    """Plugins hooking into a download must be told which activity (release)
    is being downloaded, so they can authorise or log the right version."""
    plugin = mock.Mock()
    plugin.pre_resource_download.return_value = None

    with mock.patch('ckanext.blob_storage.download_handler.plugins.PluginImplementations',
                    return_value=[plugin]):
        call_pre_download_handlers({'id': 'r'}, {'id': 'p'}, activity_id='activity-1')

    plugin.pre_resource_download.assert_called_once_with(
        {'id': 'r'}, {'id': 'p'}, activity_id='activity-1'
    )
