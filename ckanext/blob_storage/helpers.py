"""Template helpers for ckanext-blob-storage
"""
from os import path
from typing import Any, Dict, Optional

import ckan.plugins.toolkit as toolkit
from six.moves.urllib.parse import urlparse

from ckanext.authz_service.authz_binding.dataset import check_dataset_permissions
from ckanext.authz_service.authz_binding.common import OptionalCkanContext, check_entity_permissions, get_user_context, \
    normalize_id_part
from ckanext.authz_service.authz_binding.resource import RES_ENTITY_CHECKS

SERVER_URL_CONF_KEY = 'ckanext.blob_storage.storage_service_url'
STORAGE_NAMESPACE_CONF_KEY = 'ckanext.blob_storage.storage_namespace'


def resource_storage_prefix(package_name, org_name=None):
    # type: (str, Optional[str]) -> str
    """Get the resource storage prefix for a package name
    """
    if org_name is None:
        org_name = storage_namespace()
    return '{}/{}'.format(org_name, package_name)


def resource_authz_scope(package_name, actions=None, org_name=None, resource_id=None, activity_id=None):
    # type: (str, Optional[str], Optional[str], Optional[str], Optional[str]) -> str
    """Get the authorization scope for package resources
    """
    if actions is None:
        actions = 'read,write'
    if resource_id is None:
        resource_id = '*'
    scope = 'obj:{}/{}:{}'.format(
        resource_storage_prefix(package_name, org_name),
        _resource_version(resource_id, activity_id),
        actions
    )
    return scope


def _resource_version(resource_id, activity_id):
    result = resource_id
    if activity_id:
        result += "/{}".format(activity_id)
    return result


def server_url():
    # type: () -> Optional[str]
    """Get the configured server URL
    """
    url = toolkit.config.get(SERVER_URL_CONF_KEY)
    if not url:
        raise ValueError("Configuration option '{}' is not set".format(
            SERVER_URL_CONF_KEY))
    if url[-1] == '/':
        url = url[0:-1]
    return url


def storage_namespace():
    """Get the storage namespace for this CKAN instance
    """
    ns = toolkit.config.get(STORAGE_NAMESPACE_CONF_KEY)
    if ns:
        return ns
    return 'ckan'


def organization_name_for_package(package):
    # type: (Dict[str, Any]) -> Optional[str]
    """Get the organization name for a known, fetched package dict
    """
    context = {'ignore_auth': True}
    org = package.get('organization')
    if not org and package.get('owner_org'):
        org = toolkit.get_action('organization_show')(context, {'id': package['owner_org']})
    if org:
        return org.get('name')
    return None


def resource_filename(resource):
    """Get original file name from resource
    """
    if 'url' not in resource:
        return resource['name']

    if resource['url'][0:6] in {'http:/', 'https:'}:
        url_path = urlparse(resource['url']).path
        return path.basename(url_path)
    return resource['url']


def _check_resource_in_dataset(resource_id, dataset_id, context=None):
    # type: (str, str, OptionalCkanContext) -> bool
    """Check that a resource exists in the dataset
    """
    if context is None:
        context = get_user_context()
    try:
        ds = toolkit.get_action('package_show')(context, {"id": dataset_id})
        for resource in ds['resources']:
            if resource['id'] == resource_id:
                return True
    except (toolkit.ObjectNotFound, toolkit.NotAuthorized):
        pass

    return False


def activity_resource_show(context, data_dict):
    activity_id = data_dict.get('activity_id', None)
    dataset_id = data_dict.get('dataset_id', None)
    resource_id = data_dict.get('resource_id', None)

    if activity_id and dataset_id and resource_id:
        return find_activity_resource(activity_id, resource_id, dataset_id, context)[1]
    else:
        raise AttributeError("Attribute(s) not found")


def find_activity_resource(activity_id, resource_id, dataset_id, context) -> (dict, dict):
    """check if resource in a release
    """
    if activity_id and toolkit.check_ckan_version(min_version='2.9'):
        try:
            activity = toolkit.get_action(u'activity_show')(
                context, {u'id': activity_id, u'include_data': True})
            activity_dataset = activity['data']['package']

            assert (activity_dataset['name'] == dataset_id) or (activity_dataset['id'] == dataset_id)

            activity_resources = activity_dataset['resources']
            for r in activity_resources:
                if r['id'] == resource_id:
                    resource = r
                    package = activity_dataset
                    return package, resource
        except AssertionError or toolkit.NotFound:
            pass

    return None, None


def check_resource_permissions(id, dataset_id=None, organization_id=None, activity_id=None, context=None):
    """Check what resource permissions a user has
    """
    if dataset_id is None:
        return set()

    granted = check_dataset_permissions(id=dataset_id, organization_id=organization_id, context=context)
    if id == '*' or id is None:
        # Resource permissions for "all resources" can be taken from dataset permissions
        return granted.intersection(set(RES_ENTITY_CHECKS.keys()))

    if not find_activity_resource(activity_id, id, dataset_id, context=context) and \
            not _check_resource_in_dataset(resource_id=id, dataset_id=dataset_id, context=context):
        return set()

    return check_entity_permissions(RES_ENTITY_CHECKS, {"id": id}, context=context)
