"""Object storage client (MinIO/S3)."""
from minio import Minio
from vaxgenesis.config import settings

_client = Minio(
    f"{settings.minio_host}:{settings.minio_port}" if hasattr(settings, 'minio_host') else "localhost:9000",
    access_key=getattr(settings, 'minio_access_key', 'vaxgenesis'),
    secret_key=getattr(settings, 'minio_secret_key', 'vaxgenesis-secret'),
    secure=False,
)

class ObjectStorage:
    def __init__(self):
        self.client = _client
    def put_text(self, key, content, bucket="vaxgenesis", content_type="text/plain"):
        import io
        self.client.put_object(bucket, key, io.BytesIO(content.encode()), len(content), content_type=content_type)
        return f"s3://{bucket}/{key}"
    def get_text(self, key, bucket="vaxgenesis"):
        resp = self.client.get_object(bucket, key)
        return resp.read().decode()

storage = ObjectStorage()
