# CKAN 2.11 Resource Download Fix

## The Problem (Simple Explanation)

When you click "Download" on a resource in CKAN, something breaks and you get an error like:
```
TypeError: expected str, bytes or os.PathLike object, not NoneType
```

### Why Does This Happen?

Think of it like having **two doorways** to the same room:

1. **CKAN's doorway** → Expects files stored on the local disk
2. **Blob-storage's doorway** → Knows files are stored in the cloud (LFS/Giftless)

In CKAN 2.9, blob-storage's doorway was used first. But in **CKAN 2.11**, CKAN's doorway sometimes gets used first by mistake.

When CKAN's doorway is used, it asks: *"Where is this file on disk?"*  
Blob-storage answers: `None` (because the file isn't on disk - it's in the cloud!)  
CKAN then tries to open `None` as a file path → **BOOM! Error.**

## The Solution

We changed blob-storage's answer. Instead of saying `None`, it now says:

> "Hey, you're at the wrong doorway! Let me redirect you to the correct one."

This way, even if CKAN's doorway is used first, you still end up at blob-storage's doorway where the download works correctly.

## Technical Details (For Developers)

### Before (Broken)
```python
class DummyUploader:
    def get_path(self, id):
        return None  # CKAN tries flask.send_file(None) → Error!
```

### After (Fixed)
```python
class DummyUploader:
    def get_path(self, id):
        # Redirect to blob-storage's download endpoint
        raise BlobStorageRedirectException(resource_id, package_id)
```

The `BlobStorageRedirectException` is a special HTTP exception that tells Flask:
"Don't continue with this request - redirect the user to this other URL instead."

## How Routes Work in CKAN 2.11

```
User clicks Download
        ↓
URL: /dataset/my-data/resource/abc123/download
        ↓
    ┌─────────────────────────────────────┐
    │  Flask checks registered routes     │
    │                                     │
    │  1. blob_storage.download (plugin)  │  ← Registered first
    │  2. dataset_resource.download       │  ← Registered last (CKAN 2.11)
    │                                     │
    │  Both match the same URL!           │
    │  Sometimes #2 wins due to Flask's   │
    │  routing algorithm                  │
    └─────────────────────────────────────┘
        ↓
If CKAN's route wins → DummyUploader.get_path() is called
        ↓
OLD: Returns None → Error
NEW: Raises redirect → User sent to blob_storage.download → Works!
```

## Testing

Run the tests to verify:
```bash
pytest ckanext/blob_storage/tests/test_uploader.py -v
```
