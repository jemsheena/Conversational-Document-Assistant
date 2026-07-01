import os

from app.storage import LocalPDFStorage, get_pdf_storage, reset_pdf_storage


def test_local_storage_save_and_load(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    reset_pdf_storage()

    storage = LocalPDFStorage(directory=str(tmp_path))
    content = b"%PDF-1.4 test"
    uri = storage.save_pdf(content, "abc123")

    assert uri.endswith("abc123.pdf")
    assert storage.load_pdf("abc123") == content

    storage.delete_pdf("abc123")
    assert not os.path.exists(uri)


def test_get_pdf_storage_defaults_to_local(monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    reset_pdf_storage()
    storage = get_pdf_storage()
    assert isinstance(storage, LocalPDFStorage)
