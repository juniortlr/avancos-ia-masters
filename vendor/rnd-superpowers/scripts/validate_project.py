"""Static package checks, not a scientific-validity certificate. Requires PyYAML."""
from pathlib import Path
import re
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]


def validate(root=ROOT):
    errors, names = [], []
    for p in sorted((root/'skills').glob('*/SKILL.md')):
        text = p.read_text(encoding='utf-8')
        parts = text.split('---', 2)
        try:
            meta = yaml.safe_load(parts[1]) if len(parts) == 3 and not parts[0].strip() else None
            if not isinstance(meta, dict):
                raise ValueError('missing frontmatter')
            name = meta.get('name', '')
            if not isinstance(name, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name) or len(name)>64:
                raise ValueError('invalid skill name')
            if name != p.parent.name:
                raise ValueError('folder/name mismatch')
            if not isinstance(meta.get('description'), str) or not meta['description'].strip():
                raise ValueError('missing description')
            if len(text.splitlines()) > 500:
                raise ValueError('skill exceeds 500 lines')
            names.append(name)
        except (yaml.YAMLError, ValueError, IndexError) as exc:
            errors.append(f'{p.relative_to(root)}: {exc}')
    if len(names) != len(set(names)):
        errors.append('duplicate skill names')
    if not names:
        errors.append('no skills')
    index = (root/'skills/using-research-superpowers/SKILL.md').read_text()
    for name in names:
        if name != 'using-research-superpowers' and f'`{name}`' not in index:
            errors.append(f'{name} absent from index')
    for p in root.rglob('*.md'):
        if '.git' in p.parts:
            continue
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', p.read_text()):
            if re.match(r'^[a-z]+:',target) or target.startswith('#') or '<' in target:
                continue
            if not (p.parent/target.split('#')[0]).exists():
                errors.append(f'{p.relative_to(root)}: broken link {target}')
    return names, errors


if __name__ == '__main__':
    names, errors = validate()
    print(f'{len(names)} skills; {len(errors)} static errors')
    print('\n'.join(errors))
    sys.exit(bool(errors))
