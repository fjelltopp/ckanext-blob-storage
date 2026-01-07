# Migration Progress: ckanext-blob-storage

## Batch 1: Package Installation Issues

### Issue 1: Circular import in setup.py

**Error Message:**
```
ModuleNotFoundError: No module named 'ckanext.blob_storage'
ERROR: Failed to build 'file:///...' when getting requirements to build editable
```

**Root Cause:**
- `setup.py` line 6 imports `ckanext.blob_storage` before the package is installed
- Line 20 uses `ckanext.blob_storage.__version__` to get the version
- This creates a circular dependency during editable installation

**Solution Applied:**
- Removed `import ckanext.blob_storage` from setup.py
- Added `import re` for regex pattern matching
- Created `get_version()` function that reads version from `__init__.py` using file I/O and regex
- Changed `version=ckanext.blob_storage.__version__` to `version=version`

**Files Modified:**
- `setup.py`: Replaced module import with file-based version reading

**Result:**
✅ FIXED - Package installation successful

### Issue 2: Dependency version conflicts

**Error Message:**
```
ImportError: cannot import name 'TypeVar' from 'typing_extensions'

ERROR: pip's dependency resolver conflicts:
- exceptiongroup requires typing-extensions>=4.6.0, but you have 4.2.0
- flask requires click>=8.1.3, but you have 8.1.2
- responses requires requests>=2.30.0, but you have 2.27.1
```

**Root Cause:**
- `requirements.txt` had outdated pinned versions
- `typing-extensions==4.2.0` (CKAN needs >=4.6.0)
- `click==8.1.2` (Flask needs >=8.1.3)
- `requests==2.27.1` (responses needs >=2.30.0)
- These old versions are incompatible with CKAN 2.11 dependencies

**Solution Applied:**
Updated `requirements.txt` with compatible versions:
- `certifi`: 2021.10.8 → 2024.7.4
- `charset-normalizer`: 2.0.12 → 3.3.2
- `click`: 8.1.2 → 8.1.3
- `idna`: 3.3 → 3.7
- `python-dateutil`: 2.8.2 → 2.9.0
- `requests`: 2.27.1 → 2.32.3
- `typing-extensions`: 4.2.0 → 4.12.2
- `urllib3`: 1.26.9 → 2.2.2

**Files Modified:**
- `requirements.txt`: Updated dependency versions to match CKAN 2.11 requirements

**Result:**
✅ FIXED - Dependencies updated, no more conflicts

### Issue 3: Removed plugin in CKAN 2.11

**Error Message:**
```
ckan.plugins.base.PluginNotFoundException: Interface recline_view does not exist
```

**Root Cause:**
- `test.ini` includes `recline_view` in the plugins list
- `recline_view` plugin was removed in CKAN 2.11
- It was deprecated and removed from the core CKAN plugins

**Solution Applied:**
- Removed `recline_view` from the `ckan.plugins` list in `test.ini`
- Plugin list now: `stats text_view image_view authz_service blob_storage`

**Files Modified:**
- `test.ini`: Line 15 - Removed deprecated recline_view plugin

**Result:**
✅ FIXED - Removed deprecated plugin

### Issue 4: Python 3.10 incompatibility in external dependency

**Error Message:**
```
ImportError: cannot import name 'Iterable' from 'collections' (/usr/local/lib/python3.10/collections/__init__.py)
```

**Root Cause:**
- External dependency `ckanext-authz-service` has Python 3.10 incompatibility
- In Python 3.10+, `Iterable` moved from `collections` to `collections.abc`
- File `/usr/local/lib/python3.10/site-packages/ckanext/authz_service/authzzie.py` line 12:
  - Has: `from collections import Iterable, defaultdict`
  - Needs: `from collections.abc import Iterable`

**Solution Applied:**
- Added post-install patch in `.github/workflows/test.yaml`
- Uses `sed` to split the imports after installing ckanext-authz-service
- Changes `from collections import Iterable, defaultdict` to:
  - `from collections.abc import Iterable`
  - `from collections import defaultdict`
- Only `Iterable` moves to `collections.abc`; `defaultdict` stays in `collections`

**Files Modified:**
- `.github/workflows/test.yaml`: Line 61 - Added Python 3.10 compatibility patch

**Note:**
This is a temporary workaround. Long-term solution would be to use a Python 3.10 compatible fork of ckanext-authz-service or update the upstream repository.

**Result:**
✅ FIXED - Python 3.10 compatibility patch applied

### Issue 5: pytest-cov incompatible with old pluggy version

**Error Message:**
```
TypeError: HookimplMarker.__call__() got an unexpected keyword argument 'wrapper'
```

**Root Cause:**
- `dev-requirements.txt` has `pluggy==0.13.1` (old version)
- `pytest-cov==6.2.0` requires `pluggy>=1.0.0` for `wrapper` parameter support
- The `wrapper` parameter in hook implementation markers was added in pluggy 1.0.0
- Old pluggy version doesn't recognize this parameter, causing pytest-cov to fail

**Solution Applied:**
- Updated `pluggy` version in `dev-requirements.txt`
- Changed from `0.13.1` to `1.5.0` (latest stable version)
- Added comment explaining the pytest-cov compatibility requirement

**Files Modified:**
- `dev-requirements.txt`: Line 38-39 - Updated pluggy to 1.5.0

**Result:**
Ready for testing - awaiting user confirmation
