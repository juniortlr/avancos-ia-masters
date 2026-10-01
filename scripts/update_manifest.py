"""Refresh hashes of tracked and unignored publication files, excluding this manifest."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
names = subprocess.check_output(
    ['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT
).decode('utf8').split('\0')
names = sorted(set(n for n in names if n and n != 'publication-manifest.json'))
files = [ROOT / name for name in names if (ROOT / name).is_file()]
manifest = {
    'archive_commit': '02d110722f2aee6f9d684faa748afcd932821477',
    'framework_commit': 'f68892c8b7adba358b8aa437eec00a89fe88d340',
    'scope': 'Tarefa5 artifacts, executable Colab notebook, provided assignment and prior Overleaf references',
    'files': [{'path': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size,
               'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in files],
}
(ROOT / 'publication-manifest.json').write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf8', newline='\n')
print(json.dumps({'files': len(files), 'bytes': sum(p.stat().st_size for p in files)}))
