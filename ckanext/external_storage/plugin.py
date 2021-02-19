import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.authz_service.authzzie import Authzzie
from ckanext.authz_service.interfaces import IAuthorizationBindings

from . import actions, authz, helpers
from .blueprints import blueprint
from .download_handler import download_handler
from .interfaces import IResourceDownloadHandler
from ckan.lib.plugins import DefaultTranslation


class ExternalStoragePlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IActions)
    plugins.implements(IAuthorizationBindings)
    plugins.implements(IResourceDownloadHandler, inherit=True)

    # IConfigurer

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('webassets', 'external_storage')

    # ITemplateHelpers

    def get_helpers(self):
        return {'extstorage_server_url': helpers.server_url,
                'extstorage_resource_authz_scope': helpers.resource_authz_scope,
                'extstorage_resource_storage_prefix': helpers.resource_storage_prefix,
                'extstorage_storage_namespace': helpers.storage_namespace,
                'extstorage_use_scheming_file_uploader': helpers.use_scheming_file_uploader}

    # IBlueprint

    def get_blueprint(self):
        return blueprint

    # IActions

    def get_actions(self):
        return {
            'get_resource_download_spec': actions.get_resource_download_spec,
            'resource_schema_show': actions.resource_schema_show,
            'resource_sample_show': actions.resource_sample_show
        }

    # IAuthorizationBindings

    def register_authz_bindings(self, authorizer):
        # type: (Authzzie) -> None
        """Authorization Bindings

        This aliases CKANs Resource entity and actions to scopes understood by
        Giftless' JWT authorization scheme
        """
        # Register object authorization bindings
        authorizer.register_entity_ref_parser('obj', authz.object_id_parser)
        authorizer.register_authorizer('obj', authz.check_object_permissions,
                                       actions={'update', 'read'},
                                       subscopes=(None, 'data', 'metadata'))
        authorizer.register_action_alias('write', 'update', 'obj')
        authorizer.register_scope_normalizer('obj', authz.normalize_object_scope)

    # IResourceDownloadHandler

    def resource_download(self, resource, package, filename=None):
        return download_handler(resource, package, filename)
