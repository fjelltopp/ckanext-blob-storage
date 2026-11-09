class DummyUploader(object):
    """Dummy IUploader for blob-storage.

    This class implements a dummy IUploader interface which allows extensions
    like ckanext-validation to detect that there's a non-standard storage
    plugin used in CKAN.

    Files are stored in an LFS server, never on the CKAN disk, so there is no
    local path to return. Downloads are served by the ``blob_storage.download``
    view (see blueprints.py). If CKAN core's own download view ever calls
    get_path(), the request was routed to the wrong view: fail loudly.
    """

    def __init__(self, resource):
        self.resource = resource

    def get_path(self, id):
        raise NotImplementedError(
            'Resource {} is stored in blob storage and has no local path. '
            'Downloads must be served by the blob_storage.download view; '
            'CKAN core download view was reached instead (route conflict?).'.format(id)
        )

    def upload(self, id, max_size):
        return None
