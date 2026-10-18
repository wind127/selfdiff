"""Inspect the artifacts actually shipped, not just the source checkout."""
from pathlib import Path, PurePosixPath
import hashlib
import sys
import tarfile
import zipfile


def check(folder):
    artifacts=sorted(Path(folder).glob('selfdiff-*.whl'))+sorted(Path(folder).glob('selfdiff-*.tar.gz'))
    assert len(artifacts)==2, 'Expected one wheel and one source distribution'
    for artifact in artifacts:
        if artifact.suffix=='.whl':
            with zipfile.ZipFile(artifact) as z:
                names=z.namelist()
        else:
            with tarfile.open(artifact) as t:
                names=t.getnames()
        for name in names:
            parts=PurePosixPath(name).parts
            assert not {'node_modules','.venv','.local','.superpowers','imports','reports'}.intersection(parts), name
            assert not any(p.startswith('.env') or p.endswith(('.db','.sqlite3','.sqlite3-wal','.sqlite3-shm')) for p in parts), name
        assert any(n.endswith('selfdiff/static/index.html') for n in names), 'Missing installed frontend'
        assert any('/static/assets/' in n and n.endswith('.js') for n in names), 'Missing browser JS'
        assert any(n.endswith('selfdiff/data/demo.json') for n in names), 'Missing synthetic demo'
        print(artifact.name,artifact.stat().st_size,hashlib.sha256(artifact.read_bytes()).hexdigest())
    return artifacts


if __name__=='__main__':
    check(sys.argv[1] if len(sys.argv)>1 else 'dist')
