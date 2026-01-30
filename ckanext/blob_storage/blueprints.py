"""ckanext-blob-storage Flask blueprints
"""
from ckan.plugins import toolkit
from flask import Blueprint, request

from .download_handler import call_download_handlers, call_pre_download_handlers, get_context
from .helpers import find_activity_package, find_activity_resource
blueprint = Blueprint(
    'blob_storage',
    __name__,
)


def download(id, resource_id, filename=None, package_type=None):
    """Download resource blueprint

    This calls all registered download handlers in order, until
    a response is returned to the user.

    The package_type parameter is captured but not used - it allows this
    route to handle downloads for any package type (dataset, dataset-2, etc.)
    """
    context = get_context()
    activity_id = request.args.get('activity_id')

    try:
        if activity_id:
            package = find_activity_package(context, activity_id, resource_id, id)
            resource = find_activity_resource(context, activity_id, resource_id, id)
        else:
            package = toolkit.get_action('package_show')(context, {'id': id})
            resource = toolkit.get_action('resource_show')(context, {'id': resource_id})

        if id != resource['package_id']:
            return toolkit.abort(404, toolkit._('Resource not found belonging to package'))
    except toolkit.ObjectNotFound:
        return toolkit.abort(404, toolkit._('Resource not found'))
    except toolkit.NotAuthorized:
        return toolkit.abort(401, toolkit._('Not authorized to read resource {0}'.format(id)))
    except toolkit.NotFound:
        toolkit.abort(404, toolkit._(u'Activity not found'))

    inline = toolkit.asbool(request.args.get('preview'))

    try:
        resource = call_pre_download_handlers(resource, package, activity_id=activity_id)
        return call_download_handlers(resource, package, filename, inline, activity_id=activity_id)
    except toolkit.ObjectNotFound:
        return toolkit.abort(404, toolkit._('Resource not found'))
    except toolkit.NotAuthorized:
        return toolkit.abort(401, toolkit._('Not authorized to read resource {0}'.format(resource_id)))


# Routes for any package type (dataset, dataset-2, etc.)
# strict_slashes=False allows matching with or without trailing slash
blueprint.add_url_rule(u'/<package_type>/<id>/resource/<resource_id>/download', view_func=download, strict_slashes=False)
blueprint.add_url_rule(u'/<package_type>/<id>/resource/<resource_id>/download/<filename>', view_func=download)
