"""Collect an isolated validation run, omitting cache/runtime internals."""
import argparse
from pathlib import Path
import shutil

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--destination', type=Path, required=True)
args = parser.parse_args()
assert (args.source / 'linux-smoke-validation.json').is_file()
shutil.copytree(args.source, args.destination,
    ignore=shutil.ignore_patterns('ray-storage', '__pycache__', '.matplotlib'))
print(args.destination)
