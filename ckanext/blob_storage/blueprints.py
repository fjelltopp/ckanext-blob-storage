"""ckanext-blob-storage Flask blueprints
"""
from ckan.plugins import toolkit
from flask import Blueprint, request

from .download_handler import call_download_handlers, call_pre_download_handlers, get_context
from . import helpers

blueprint = Blueprint(
    'blob_storage',
    __name__,
)


def download(id, resource_id, filename=None):
    """Download resource blueprint

    This calls all registered download handlers in order, until
    a response is returned to the user
    """

    # we will check if the resource was not found
    not_found_in_package = False
    context = get_context()
    resource = package = {}

    try:
        resource = toolkit.get_action('resource_show')(context, {'id': resource_id})
        if id != resource['package_id']:
            return toolkit.abort(404, toolkit._('Resource not found belonging to package'))
        package = toolkit.get_action('package_show')(context, {'id': id})
    except toolkit.ObjectNotFound:
        not_found_in_package = True
    except toolkit.NotAuthorized:
        return toolkit.abort(401, toolkit._('Not authorized to read resource {0}'.format(id)))

    activity_id = request.args.get('activity_id')
    inline = toolkit.asbool(request.args.get('preview'))

    if not_found_in_package:
        _, package, resource = helpers.find_activity_resource(activity_id, id, resource_id, get_context())

    try:
        resource = call_pre_download_handlers(resource, package, activity_id=activity_id)
        return call_download_handlers(resource, package, filename, inline, activity_id=activity_id)
    except toolkit.ObjectNotFound:
        return toolkit.abort(404, toolkit._('Resource not found'))
    except toolkit.NotAuthorized:
        return toolkit.abort(401, toolkit._('Not authorized to read resource {0}'.format(resource_id)))


blueprint.add_url_rule(u'/dataset/<id>/resource/<resource_id>/download', view_func=download)
blueprint.add_url_rule(u'/dataset/<id>/resource/<resource_id>/download/<filename>', view_func=download)
