"""Audit one predictive split from a CSV manifest; does not inspect feature values.

Required columns: row_id, entity_id, split (train/validation/test), prediction_time,
label_end, feature_available_at. Times must be timezone-aware ISO 8601.
For each split boundary, all training labels must mature before evaluation origins.
Use --disjoint-entities only when claiming generalization to unseen entities.
"""
import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

REQUIRED = {'row_id', 'entity_id', 'split', 'prediction_time', 'label_end', 'feature_available_at'}
ORDER = ('train', 'validation', 'test')


def time_value(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('timestamps must include timezone offsets')
    return result


def audit(rows, disjoint_entities=False):
    errors = []
    if not rows:
        return {'passed': False, 'errors': ['empty manifest'], 'rows': 0}
    missing = REQUIRED - set(rows[0])
    if missing:
        return {'passed': False, 'errors': ['missing columns: '+', '.join(sorted(missing))], 'rows': len(rows)}
    seen = set()
    groups = {key: [] for key in ORDER}
    for i, row in enumerate(rows, 2):
        if not row['row_id'] or row['row_id'] in seen:
            errors.append(f'row {i}: missing or duplicate row_id')
        seen.add(row['row_id'])
        if not row['entity_id']:
            errors.append(f'row {i}: missing entity_id')
        if row['split'] not in groups:
            errors.append(f'row {i}: unknown split')
            continue
        try:
            origin, end, available = [time_value(row[k]) for k in ('prediction_time','label_end','feature_available_at')]
        except (ValueError, TypeError, AttributeError):
            errors.append(f'row {i}: invalid or timezone-naive timestamp')
            continue
        if available > origin:
            errors.append(f'row {i}: feature unavailable at prediction origin')
        if end < origin:
            errors.append(f'row {i}: label ends before prediction origin')
        groups[row['split']].append((row['entity_id'], origin, end))
    if not groups['train'] or not (groups['validation'] or groups['test']):
        errors.append('need training and at least one evaluation split')
    for i, left in enumerate(ORDER):
        for right in ORDER[i+1:]:
            a, b = groups[left], groups[right]
            if not a or not b:
                continue
            if max(x[2] for x in a) >= min(x[1] for x in b):
                errors.append(f'{left} labels overlap {right} origins (strict boundary required)')
            if disjoint_entities and {x[0] for x in a} & {x[0] for x in b}:
                errors.append(f'{left}/{right} entity overlap')
    return {'passed': not errors, 'errors': errors, 'rows': len(rows),
            'entities': len({r['entity_id'] for r in rows}),
            'disjoint_entities_required': disjoint_entities,
            'scope': 'one supplied split; does not prove feature lineage, target validity or every AutoML internal fold'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--disjoint-entities', action='store_true')
    args = parser.parse_args()
    with args.manifest.open(newline='', encoding='utf-8') as f:
        result = audit(list(csv.DictReader(f)), args.disjoint_entities)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()
