from io import BytesIO
import zipfile
import pytest
from selfdiff.sources.ingest import preview_upload, preview_path
from selfdiff.errors import AppError
from test_repository import sample


def zipped(names):
    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for name in names:
            z.writestr(name, sample())
    return buf.getvalue()


def test_preview_is_read_only(tmp_path):
    path = tmp_path / '输入.json'
    path.write_bytes(sample())
    preview = preview_path('normalized', path)
    assert preview.message_count == 1
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize('name', ['../escape.json', '/absolute.json', 'C:/escape.json', 'a/../../x.json', 'a\\..\\x.json'])
def test_zip_rejects_traversal(name):
    with pytest.raises(AppError):
        preview_upload('normalized', 'x.zip', zipped([name]))


def test_zip_rejects_excess_files():
    with pytest.raises(AppError):
        preview_upload('normalized', 'x.zip', zipped([f'{i}.json' for i in range(201)]))


def test_zip_and_file_size_limits(monkeypatch):
    import selfdiff.sources.ingest as ingest
    monkeypatch.setattr(ingest, 'MAX_FILE', 10)
    with pytest.raises(AppError):
        preview_upload('normalized', 'x.json', sample())
    monkeypatch.setattr(ingest, 'MAX_FILE', 5000)
    monkeypatch.setattr(ingest, 'MAX_EXPANDED', 10)
    with pytest.raises(AppError):
        preview_upload('normalized', 'x.zip', zipped(['a.json']))


def test_zip_symlinks_rejected():
    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        info = zipfile.ZipInfo('link.json')
        info.create_system = 3
        info.external_attr = 0o120777 << 16
        z.writestr(info, 'outside')
    with pytest.raises(AppError):
        preview_upload('normalized', 'x.zip', buf.getvalue())
