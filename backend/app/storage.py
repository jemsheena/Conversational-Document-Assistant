"""PDF storage backends: local disk (dev) or AWS S3 (production)."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Optional

from app.config import settings


class PDFStorage(ABC):
    @abstractmethod
    def save_pdf(self, content: bytes, file_hash: str) -> str:
        """Persist PDF bytes. Returns a URI (file path or s3://...)."""

    @abstractmethod
    def load_pdf(self, file_hash: str) -> bytes:
        """Load PDF bytes by content hash."""

    @abstractmethod
    def delete_pdf(self, file_hash: str) -> None:
        """Remove a stored PDF if it exists."""


class LocalPDFStorage(PDFStorage):
    def __init__(self, directory: str | None = None) -> None:
        self.directory = directory or settings.PDF_STORAGE_DIR
        os.makedirs(self.directory, exist_ok=True)

    def _path(self, file_hash: str) -> str:
        return os.path.join(self.directory, f"{file_hash}.pdf")

    def save_pdf(self, content: bytes, file_hash: str) -> str:
        path = self._path(file_hash)
        with open(path, "wb") as f:
            f.write(content)
        return path

    def load_pdf(self, file_hash: str) -> bytes:
        path = self._path(file_hash)
        if not os.path.exists(path):
            raise FileNotFoundError(f"PDF not found: {path}")
        with open(path, "rb") as f:
            return f.read()

    def delete_pdf(self, file_hash: str) -> None:
        path = self._path(file_hash)
        if os.path.exists(path):
            os.remove(path)


class S3PDFStorage(PDFStorage):
    def __init__(
        self,
        bucket: str,
        prefix: str = "pdfs/",
        region: str | None = None,
    ) -> None:
        import boto3

        self.bucket = bucket
        self.prefix = prefix if prefix.endswith("/") or not prefix else f"{prefix}/"
        self.region = region or settings.AWS_REGION
        self._client = boto3.client("s3", region_name=self.region)

    def _key(self, file_hash: str) -> str:
        return f"{self.prefix}{file_hash}.pdf"

    def uri(self, file_hash: str) -> str:
        return f"s3://{self.bucket}/{self._key(file_hash)}"

    def save_pdf(self, content: bytes, file_hash: str) -> str:
        self._client.put_object(
            Bucket=self.bucket,
            Key=self._key(file_hash),
            Body=content,
            ContentType="application/pdf",
        )
        return self.uri(file_hash)

    def load_pdf(self, file_hash: str) -> bytes:
        response = self._client.get_object(Bucket=self.bucket, Key=self._key(file_hash))
        return response["Body"].read()

    def delete_pdf(self, file_hash: str) -> None:
        self._client.delete_object(Bucket=self.bucket, Key=self._key(file_hash))


_storage: Optional[PDFStorage] = None


def get_pdf_storage() -> PDFStorage:
    global _storage
    if _storage is not None:
        return _storage

    backend = settings.STORAGE_BACKEND.lower()
    if backend == "s3":
        if not settings.S3_BUCKET:
            raise ValueError("S3_BUCKET is required when STORAGE_BACKEND=s3")
        _storage = S3PDFStorage(
            bucket=settings.S3_BUCKET,
            prefix=settings.S3_PREFIX,
            region=settings.AWS_REGION,
        )
    else:
        _storage = LocalPDFStorage()

    return _storage


def reset_pdf_storage() -> None:
    """Clear cached storage instance (for tests)."""
    global _storage
    _storage = None
