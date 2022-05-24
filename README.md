
**s3_usecases_npcmr** - a set of use cases of boto3 wrapped into a module.

# Content
  - [Installation](#installation)
  - [Usage](#usage)
  - [Dependences](#dependences)
  - [TODO](#todo)


# Installation
```
pip install s3_npcmr
```


# Usage
Create your own class inheriting from ObjectStorage, set params.
```python
from s3_npcmr import ObjectStorage as BaseObjectStorage

class ObjectStorage(BaseObjectStorage):
  S3_SERVICE_NAME = 'YOUR_PARAM'
  S3_ENDPOINT_URL = 'YOUR_PARAM'
  S3_BUCKET = 'YOUR_PARAM'
  REDIS_CONTAINER_NAME = 'YOUR_PARAM'
```

Upload a file
```python
s3 = ObjectStorage()
s3.upload_file(file_as_bytes, unique_s3_key_for_this_file)
```

Get metadata
```python
s3 = ObjectStorage()
data = s3.get_metadata(obj.s3_key).get('Metadata', {})
metadata =  {k.lower(): v for k, v in data.items()}
```

Get hashed links to files
```python
s3 = ObjectStorage()
file_urls['watch'] = s3.get_presigned_url(obj.s3_key)
file_urls['download'] = s3.get_presigned_url(obj.s3_key, 'attachment')
```


# Dependences
- boto3
- Redis (241.2 kB)


# TODO
- make redis optional