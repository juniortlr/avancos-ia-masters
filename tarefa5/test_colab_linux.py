"""Execute the exact Colab notebook in a fresh Linux kernel; never claims hosted testing."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import tempfile
import time

import nbformat
from nbclient import NotebookClient


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--notebook', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert platform.system() == 'Linux', 'This validation is specifically a Linux run'
    args.workspace.mkdir(parents=True, exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)
    source_bytes = args.notebook.read_bytes()
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    nb = nbformat.reads(source_bytes.decode('utf8'), as_version=4)
    nbformat.validate(nb)
    started = time.monotonic()
    completed = []

    def progress(cell, cell_index, **kwargs):
        if cell.cell_type == 'code':
            completed.append(cell_index)
            print(f'Executed notebook cell {cell_index}', flush=True)

    with tempfile.TemporaryDirectory(prefix='aula05-kernel-') as temp:
        kernel_dir = Path(temp) / 'kernels' / 'aula05validation'
        kernel_dir.mkdir(parents=True)
        (kernel_dir / 'kernel.json').write_text(json.dumps({
            'argv': [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
            'display_name': 'Linux validation', 'language': 'python'}))
        previous = os.environ.get('JUPYTER_PATH')
        os.environ['JUPYTER_PATH'] = str(Path(temp)) + (os.pathsep + previous if previous else '')
        nb.metadata.kernelspec = {'name': 'aula05validation', 'display_name': 'Linux validation', 'language': 'python'}
        failure = None
        try:
            NotebookClient(nb, timeout=2400, kernel_name='aula05validation',
                resources={'metadata': {'path': str(args.workspace)}},
                on_cell_executed=progress).execute()
        except Exception as error:
            failure = f'{type(error).__name__}: {error}'
            raise
        finally:
            if previous is None:
                os.environ.pop('JUPYTER_PATH', None)
            else:
                os.environ['JUPYTER_PATH'] = previous
            nb.metadata.kernelspec = {'name': 'python3', 'display_name': 'Python 3', 'language': 'python'}
            nb.metadata['validation_environment'] = 'Local Linux / WSL; not hosted Google Colab'
            nbformat.write(nb, args.output / 'analysis_executed.ipynb')
            cells = [c for c in nb.cells if c.cell_type == 'code']
            report = {
                'status': 'failed' if failure else 'passed', 'failure': failure,
                'environment': 'Local Linux / WSL; not hosted Google Colab',
                'kernel_python': sys.version, 'platform': platform.platform(),
                'notebook_sha256': source_sha256,
                'code_cells': len(cells), 'executed_cells': sum(c.execution_count is not None for c in cells),
                'error_outputs': sum(o.output_type == 'error' for c in cells for o in c.outputs),
                'embedded_pngs': sum('image/png' in o.get('data', {}) for c in cells for o in c.outputs),
                'elapsed_seconds': time.monotonic() - started,
            }
            (args.output / 'validation.json').write_text(json.dumps(report, indent=2), encoding='utf8')
            print(json.dumps({k: v for k, v in report.items() if k != 'failure'}), flush=True)


if __name__ == '__main__':
    main()
