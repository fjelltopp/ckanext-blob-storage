from ckan.plugins import toolkit
from flask import request
from werkzeug.exceptions import HTTPException


class BlobStorageRedirectException(HTTPException):
    """Exception raised to redirect to blob-storage download endpoint.

    CKAN 2.11: When CKAN core's download view is called for blob-storage
    resources, we raise this exception to trigger a redirect to the proper
    blob-storage download endpoint.
    """

    def __init__(self, resource_id, package_id, filename=None):
        self.resource_id = resource_id
        self.package_id = package_id
        self.filename = filename
        super().__init__()

    def get_response(self, environ=None):
        from flask import redirect
        # Extract package_type from the current request path
        # Path format: /<package_type>/<id>/resource/<resource_id>/download/...
        path_parts = request.path.strip('/').split('/')
        package_type = path_parts[0] if path_parts else 'dataset'
        url = toolkit.url_for(
            'blob_storage.download',
            package_type=package_type,
            id=self.package_id,
            resource_id=self.resource_id,
            filename=self.filename
        )
        return redirect(url)


class DummyUploader(object):
    """Dummy IUploader for blob-storage.

    This class implements a dummy IUploader interface which allows extensions
    like ckanext-validation to detect that there's a non-standard storage
    plugin used in CKAN.

    CKAN 2.11: If CKAN core's download view is called (due to route conflicts),
    get_path() raises an exception that triggers a redirect to blob-storage's
    download endpoint.
    """

    def __init__(self, resource):
        self.resource = resource

    def get_path(self, id):
        """Get path for the resource.

        For blob-storage resources, we redirect to the blob-storage download
        endpoint since files are stored in LFS, not locally.
        """
        # Raise redirect exception to forward to blob-storage download
        package_id = self.resource.get('package_id')
        if package_id:
            raise BlobStorageRedirectException(
                resource_id=id,
                package_id=package_id,
                filename=self.resource.get('name')
            )
        # Fallback: return None (will cause an error, but better than silent failure)
        return None

    def upload(self, id, max_size):
        return None
