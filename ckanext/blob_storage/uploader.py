from werkzeug.exceptions import HTTPException


class BlobStorageRedirectException(HTTPException):
    """Exception raised to handle blob-storage downloads.

    CKAN 2.11: When CKAN core's download view is called for blob-storage
    resources, we raise this exception to fetch the LFS download URL and
    redirect directly to Azure blob storage.
    """

    def __init__(self, resource_id, package_id, filename=None, resource=None):
        self.resource_id = resource_id
        self.package_id = package_id
        self.filename = filename
        self.resource = resource or {}
        super().__init__()

    def get_response(self, environ=None):
        # Fetch LFS download URL directly and redirect to blob storage
        # This avoids the redirect loop with CKAN's routes
        from flask import redirect, Response
        from ckan import model
        from ckan.plugins import toolkit
        from . import helpers
        from .actions import get_download_authz_token

        context = {"model": model, "ignore_auth": True}

        try:
            resource = toolkit.get_action("resource_show")(context, {"id": self.resource_id})
            package = toolkit.get_action("package_show")(context, {"id": self.package_id})

            # Get authorization token for LFS
            authz_token = get_download_authz_token(
                context,
                package["organization"]["name"],
                package["name"],
                resource["id"]
            )

            # Request download URL from LFS server
            from giftless_client import LfsClient
            client = LfsClient(helpers.server_url(), authz_token)

            resources = [{
                "oid": resource["sha256"],
                "size": resource["size"],
                "x-filename": helpers.resource_filename(resource)
            }]

            batch_response = client.batch(resource["lfs_prefix"], "download", resources)
            object_spec = batch_response["objects"][0]

            if "error" in object_spec:
                return Response(f"LFS error: {object_spec['error']}", status=404)

            href = object_spec["actions"]["download"]["href"]
            return redirect(href)

        except Exception as e:
            return Response(f"Download failed: {e}", status=500)


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
        # Raise exception to handle download via LFS
        package_id = self.resource.get('package_id')
        if package_id:
            raise BlobStorageRedirectException(
                resource_id=id,
                package_id=package_id,
                filename=self.resource.get('name'),
                resource=self.resource
            )
        # Fallback: return None (will cause an error, but better than silent failure)
        return None

    def upload(self, id, max_size):
        return None
