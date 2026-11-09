"""ckanext-blob-storage Flask blueprints
"""
from ckan import plugins
from ckan.plugins import toolkit
from flask import Blueprint, request

from .download_handler import call_download_handlers, call_pre_download_handlers, get_context
from .helpers import find_activity_package, find_activity_resource


def download(id, resource_id, filename=None, package_type=None):
    """Download resource blueprint

    This calls all registered download handlers in order, until
    a response is returned to the user.

    The package_type parameter is supplied by the route defaults (see
    make_blueprint) and is not otherwise used.
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

        if not package or not resource:
            # e.g. the resource did not exist in that activity
            return toolkit.abort(404, toolkit._('Resource not found'))

        if id != resource['package_id']:
            return toolkit.abort(404, toolkit._('Resource not found belonging to package'))
    except toolkit.ObjectNotFound:
        return toolkit.abort(404, toolkit._('Resource not found'))
    except toolkit.NotAuthorized:
        return toolkit.abort(401, toolkit._('Not authorized to read resource {0}'.format(id)))

    inline = toolkit.asbool(request.args.get('preview'))

    try:
        resource = call_pre_download_handlers(resource, package, activity_id=activity_id)
        return call_download_handlers(resource, package, filename, inline, activity_id=activity_id)
    except toolkit.ObjectNotFound:
        return toolkit.abort(404, toolkit._('Resource not found'))
    except toolkit.NotAuthorized:
        return toolkit.abort(401, toolkit._('Not authorized to read resource {0}'.format(resource_id)))


def get_package_types():
    """All package types CKAN will serve resource routes for.

    Mirrors ckan.lib.plugins.register_package_blueprints(), which registers a
    set of routes per package type, plus the generic `dataset` routes.
    """
    package_types = ['dataset']
    for plugin in plugins.PluginImplementations(plugins.IDatasetForm):
        for package_type in plugin.package_types():
            if package_type not in package_types:
                package_types.append(package_type)
    return package_types


def make_blueprint(package_types):
    """Build the blueprint serving resource downloads for the given package types.

    CKAN core registers a route with a fixed prefix for every package type, e.g.
    ``/dataset-2/<id>/resource/<resource_id>/download``. A route with a
    ``/<package_type>/`` wildcard would always lose against those, because
    Werkzeug prefers routes with more fixed text. So we register one fixed
    prefix route per package type instead: plugin blueprints are registered
    before core's, so on equally specific routes ours wins.

    CKAN generates download URLs of the form ``/<package_type>/...`` (2.11+),
    so every package type needs its own route here.
    """
    blueprint = Blueprint('blob_storage', __name__)
    for package_type in package_types:
        defaults = {'package_type': package_type}
        prefix = u'/{}/<id>/resource/<resource_id>/download'.format(package_type)
        # strict_slashes=False allows matching with or without trailing slash
        blueprint.add_url_rule(prefix, view_func=download, strict_slashes=False, defaults=defaults)
        blueprint.add_url_rule(prefix + u'/<filename>', view_func=download, defaults=defaults)
    return blueprint
