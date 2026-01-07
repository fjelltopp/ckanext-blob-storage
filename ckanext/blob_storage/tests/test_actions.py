import ckan.plugins.toolkit as toolkit
import pytest
from ckan.tests import factories, helpers


@pytest.mark.usefixtures("clean_db", "with_plugins")
def test_validation_error_if_not_sha256():
    user = factories.User()
    org = factories.Organization(user=user)
    
    with pytest.raises(toolkit.ValidationError):
        helpers.call_action(
            'package_create',
            context={'user': user['name']},
            name='test-dataset',
            owner_org=org['id'],
            resources=[
                {
                    'url': '/my/file.csv',
                    'url_type': 'upload',
                    'size': 12345,
                    'lfs_prefix': 'lfs/prefix'
                    # sha256 is intentionally missing to trigger validation error
                }
            ]
        )


@pytest.mark.usefixtures("clean_db", "with_plugins")
def test_validation_error_if_not_size_on_uploads():
    user = factories.User()
    org = factories.Organization(user=user)
    
    with pytest.raises(toolkit.ValidationError):
        helpers.call_action(
            'package_create',
            context={'user': user['name']},
            name='test-dataset-size',
            owner_org=org['id'],
            resources=[
                {
                    'url': '/my/file.csv',
                    'url_type': 'upload',
                    'sha256': 'cc71500070cf26cd6e8eab7c9eec3a937be957d144f445ad24003157e2bd0919',
                    'lfs_prefix': 'lfs/prefix'
                    # size is intentionally missing to trigger validation error
                }
            ]
        )


@pytest.mark.usefixtures("clean_db", "with_plugins")
def test_validation_error_if_not_lfs_prefix_on_uploads():
    user = factories.User()
    org = factories.Organization(user=user)
    
    with pytest.raises(toolkit.ValidationError):
        helpers.call_action(
            'package_create',
            context={'user': user['name']},
            name='test-dataset-lfs-prefix',
            owner_org=org['id'],
            resources=[
                {
                    'url': '/my/file.csv',
                    'url_type': 'upload',
                    'sha256': 'cc71500070cf26cd6e8eab7c9eec3a937be957d144f445ad24003157e2bd0919',
                    'size': 123456
                    # lfs_prefix is intentionally missing to trigger validation error
                }
            ]
        )


@pytest.mark.usefixtures("clean_db")
def test_no_validation_error_if_not_upload():
    factories.Dataset(
            resources=[{'url': 'https://www.example.com', 'url_type': ''}]
        )


@pytest.mark.usefixtures("clean_db")
def test_no_validation_error_if_all_fields_are_set():
    dataset = factories.Dataset(
        resources=[
            {
                'url': '/my/file.csv',
                'url_type': 'upload',
                'sha256': 'cc71500070cf26cd6e8eab7c9eec3a937be957d144f445ad24003157e2bd0919',
                'size': 12345,
                'lfs_prefix': 'lfs/prefix'
            }
        ]
    )

    assert dataset['resources'][0]['sha256'] == 'cc71500070cf26cd6e8eab7c9eec3a937be957d144f445ad24003157e2bd0919'
    assert dataset['resources'][0]['size'] == 12345
    assert dataset['resources'][0]['lfs_prefix'] == 'lfs/prefix'


@pytest.mark.usefixtures("clean_db", "with_plugins")
def test_validation_error_if_wrong_sha256():
    user = factories.User()
    org = factories.Organization(user=user)
    
    with pytest.raises(toolkit.ValidationError):
        helpers.call_action(
            'package_create',
            context={'user': user['name']},
            name='test-dataset-wrong-sha256',
            owner_org=org['id'],
            resources=[
                {
                    'url': '/my/file.csv',
                    'url_type': 'upload',
                    'sha256': 'wrong_sha256',  # Invalid sha256 format to trigger validation error
                    'size': 123456,
                    'lfs_prefix': 'lfs/prefix'
                }
            ]
        )


@pytest.mark.usefixtures("clean_db", "with_plugins")
def test_validation_error_if_size_not_positive_integer():
    user = factories.User()
    org = factories.Organization(user=user)
    
    # Test case 1: negative size
    with pytest.raises(toolkit.ValidationError):
        helpers.call_action(
            'package_create',
            context={'user': user['name']},
            name='test-dataset-negative-size',
            owner_org=org['id'],
            resources=[
                {
                    'url': '/my/file.csv',
                    'url_type': 'upload',
                    'sha256': 'cc71500070cf26cd6e8eab7c9eec3a937be957d144f445ad24003157e2bd0919',
                    'size': -12,  # Negative size to trigger validation error
                    'lfs_prefix': 'lfs/prefix'
                }
            ]
        )

    # Test case 2: zero size
    with pytest.raises(toolkit.ValidationError):
        helpers.call_action(
            'package_create',
            context={'user': user['name']},
            name='test-dataset-zero-size',
            owner_org=org['id'],
            resources=[
                {
                    'url': '/my/file.csv',
                    'url_type': 'upload',
                    'sha256': 'cc71500070cf26cd6e8eab7c9eec3a937be957d144f445ad24003157e2bd0919',
                    'size': 0,  # Zero size to trigger validation error
                    'lfs_prefix': 'lfs/prefix'
                }
            ]
        )


@pytest.mark.usefixtures("clean_db")
def test_validation_error_if_empty_lfs_prefix():
    with pytest.raises(toolkit.ValidationError):
        factories.Dataset(
            resources=[
                {
                    'url': '/my/file.csv',
                    'url_type': 'upload',
                    'sha256': 'cc71500070cf26cd6e8eab7c9eec3a937be957d144f445ad24003157e2bd0919',
                    'size': 123456,
                    'lfs_prefix': ''
                }
            ]
        )
