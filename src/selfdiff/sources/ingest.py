from dataclasses import dataclass, field
from hashlib import sha256
from io import BytesIO
from pathlib import Path, PurePosixPath
import os
import stat
import time
import uuid
import zipfile
from selfdiff.errors import AppError
from selfdiff.models import ConversationInput
from .registry import parse_bytes

MAX_FILE = 50 * 1024 * 1024
MAX_EXPANDED = 200 * 1024 * 1024
MAX_FILES = 200
EXTENSIONS = {'.json', '.jsonl', '.md', '.txt'}


@dataclass
class ImportPreview:
    source: str
    input_hash: str
    conversations: list[ConversationInput]
    warnings: list[str]
    preview_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    created_at: float = field(default_factory=time.time)
    path: Path | None = None

    @property
    def message_count(self):
        return sum(len(c.messages) for c in self.conversations)

    def public(self):
        dates = [m.occurred_at for c in self.conversations for m in c.messages if m.occurred_at]
        return dict(preview_id=self.preview_id, source=self.source, input_hash=self.input_hash,
                    conversation_count=len(self.conversations), message_count=self.message_count,
                    known_time_range=[min(dates), max(dates)] if dates else None, warnings=self.warnings)


def _linked(path):
    s = path.lstat()
    return stat.S_ISLNK(s.st_mode) or bool(getattr(s, 'st_file_attributes', 0) & 0x400)


def _collect(source, files):
    digest, conversations, warnings, total = sha256(), [], [], 0
    for index, (name, data) in enumerate(files):
        total += len(data)
        if index >= MAX_FILES or total > MAX_EXPANDED or len(data) > MAX_FILE:
            raise AppError('limit', '资料超过文件数量或大小限制。')
        digest.update(name.encode('utf-8'))
        digest.update(sha256(data).digest())
        result = parse_bytes(source, name, data)
        conversations.extend(result.conversations)
        warnings.extend(result.warnings)
    return ImportPreview(source, digest.hexdigest(), conversations, warnings)


def _zip_files(source, data):
    with zipfile.ZipFile(BytesIO(data)) as archive:
        entries = archive.infolist()
        if len(entries) > MAX_FILES or sum(x.file_size for x in entries) > MAX_EXPANDED:
            raise AppError('limit', 'ZIP 文件数量或解压大小超过限制。')
        for info in entries:
            name = info.filename
            path = PurePosixPath(name)
            if '\\' in name or ':' in name or path.is_absolute() or '..' in path.parts or stat.S_ISLNK(info.external_attr >> 16):
                raise AppError('path', 'ZIP 包含不安全路径或链接。')
            if info.is_dir() or path.suffix.lower() not in EXTENSIONS:
                continue
            if source in ('chatgpt', 'claude-web') and path.name != 'conversations.json':
                continue
            if info.file_size > MAX_FILE:
                raise AppError('limit', 'ZIP 中单文件超过 50 MiB。')
            with archive.open(info) as member:
                content = member.read(MAX_FILE + 1)
            yield name, content


def preview_upload(source, filename, data):
    if len(data) > MAX_FILE:
        raise AppError('limit', '单文件超过 50 MiB。')
    try:
        files = _zip_files(source, data) if Path(filename).suffix.lower() == '.zip' else [(filename, data)]
        return _collect(source, files)
    except (zipfile.BadZipFile, RuntimeError, OSError):
        raise AppError('archive', 'ZIP 无法读取；请使用未加密的标准导出。') from None


def preview_path(source, path):
    path = Path(path).expanduser().absolute()
    try:
        if _linked(path):
            raise AppError('path', '请选择实际文件或目录，不使用链接。')
        root = path.resolve(strict=True)
        if root.is_file():
            if root.stat().st_size > MAX_FILE:
                raise AppError('limit', '单文件超过 50 MiB。')
            result = preview_upload(source, root.name, root.read_bytes())
        else:
            def files():
                for current, dirs, names in os.walk(root, followlinks=False):
                    dirs[:] = sorted(d for d in dirs if not _linked(Path(current) / d))
                    for name in sorted(names):
                        file = Path(current) / name
                        if _linked(file) or file.suffix.lower() not in EXTENSIONS:
                            continue
                        file.resolve(strict=True).relative_to(root)
                        if file.stat().st_size > MAX_FILE:
                            raise AppError('limit', '目录内单文件超过限制。')
                        yield file.relative_to(root).as_posix(), file.read_bytes()
            result = _collect(source, files())
        result.path = path
        return result
    except (OSError, ValueError):
        raise AppError('path', '所选路径不可读取或超出目录边界。') from None
