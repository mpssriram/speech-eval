"""Import a checksum-pinned dataset; stdlib only, suitable for the Docker tools image."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
import urllib.request
import zipfile


def sha(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def safe_name(name: str) -> None:
    if not name or '\\' in name or ':' in name or PurePosixPath(name).is_absolute():
        raise ValueError(f'Unsafe member: {name}')
    if any(p in ('', '.', '..') for p in name.split('/')):
        raise ValueError(f'Unsafe member: {name}')


def safe_target(data: Path, name: str) -> Path:
    safe_name(name)
    target = data / name
    for parent in (target, *target.parents):
        if parent.is_symlink(): raise ValueError(f'Dataset symlink is forbidden: {parent}')
        if parent == data: break
    if not target.resolve().is_relative_to(data.resolve()):
        raise ValueError(f'Target escapes data: {name}')
    return target


def fetch(root: Path, from_local: Path | None = None) -> int:
    root = root.resolve()
    # JSON is a YAML subset: no third-party parser needed on the host or in tests.
    config = json.loads((root / 'configs/dataset.yaml').read_text())
    inventory = json.loads((root / config['inventory']).read_text())
    data = root / 'data'
    files = inventory['files']
    missing = []
    for name, meta in files.items():
        target = safe_target(data, name)
        if target.exists():
            if not target.is_file() or target.stat().st_size != meta['bytes'] or sha(target) != meta['sha256']:
                raise ValueError(f'Existing dataset file differs; refusing overwrite: {name}')
        else: missing.append(name)
    if not missing and from_local is None:
        print(f'Dataset already verified: {len(files)} files')
        return 0
    with tempfile.TemporaryDirectory(prefix='speech-release-') as temporary:
        scratch = Path(temporary)
        if from_local is not None:
            archive = from_local.resolve()
        else:
            url = config['url']
            if not url.startswith(('https://', 'http://')):
                raise ValueError('Dataset URL is pending upload. Use --from-local or make DATA_ARCHIVE=/path/release.zip')
            archive = scratch / 'download.zip'
            with urllib.request.urlopen(url, timeout=60) as response, archive.open('xb') as output:
                # Trusted inventory bounds the download, even when URL is misconfigured.
                maximum = sum(m['bytes'] for m in files.values()) + len(files) * 2048 + 1048576
                total = 0
                while chunk := response.read(1024 * 1024):
                    total += len(chunk)
                    if total > maximum: raise ValueError('Archive exceeds expected dataset size')
                    output.write(chunk)
        if sha(archive) != config['sha256']: raise ValueError('Archive SHA-256 mismatch')
        with zipfile.ZipFile(archive) as z:
            infos = z.infolist(); names = [i.filename for i in infos]
            if len(names) != len(set(names)): raise ValueError('Duplicate archive members')
            if set(names) != set(files) | {'release_manifest.json'}:
                raise ValueError('Archive members differ from trusted inventory')
            for info in infos:
                safe_name(info.filename)
                mode = info.external_attr >> 16
                if stat.S_ISLNK(mode) or info.is_dir(): raise ValueError('Archive symlink/directory forbidden')
                maximum = (files[info.filename]['bytes'] if info.filename in files
                           else (root / config['inventory']).stat().st_size + 1024)
                if info.file_size > maximum: raise ValueError('Member exceeds trusted size')
            if json.loads(z.read('release_manifest.json')) != inventory:
                raise ValueError('Internal manifest differs from trusted inventory')
            # Verify every member before creating any destination files.
            for name, meta in files.items():
                staged = scratch / 'payload' / name
                staged.parent.mkdir(parents=True, exist_ok=True)
                with z.open(name) as source, staged.open('xb') as output:
                    shutil.copyfileobj(source, output, 1024 * 1024)
                if staged.stat().st_size != meta['bytes'] or sha(staged) != meta['sha256']:
                    raise ValueError(f'Member SHA-256 mismatch: {name}')
        for name in missing:
            target = safe_target(data, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            # Copy on the destination filesystem, close completely, then atomically
            # link without replacing an existing file. A killed process can leave
            # only an unreferenced temp directory, never a truncated dataset file.
            with tempfile.TemporaryDirectory(prefix='.release-install-', dir=target.parent) as install_dir:
                completed = Path(install_dir) / 'complete'
                with completed.open('xb') as output, (scratch / 'payload' / name).open('rb') as source:
                    shutil.copyfileobj(source, output, 1024 * 1024)
                    output.flush(); os.fsync(output.fileno())
                os.link(completed, target, follow_symlinks=False)
        print(f'Dataset verified and imported: {len(files)} files ({len(missing)} installed)')
        return len(missing)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--from-local', type=Path)
    args = parser.parse_args()
    fetch(args.root, args.from_local)
