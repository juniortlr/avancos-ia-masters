"""Read-only validation of the delivered notebook, figures and report."""
from pathlib import Path
import hashlib
import json
import re
import fitz
import nbformat

ROOT = Path(__file__).resolve().parent


def main():
    notebook_path = ROOT / 'Aula05_Tarefa5_Resultados.ipynb'
    notebook = nbformat.read(notebook_path, as_version=4)
    nbformat.validate(notebook)
    code = [c for c in notebook.cells if c.cell_type == 'code']
    assert all(c.execution_count is not None for c in code), 'Unexecuted code cell'
    errors = [o for c in code for o in c.outputs if o.output_type == 'error']
    assert not errors, errors
    pngs = sum('image/png' in o.get('data', {}) for c in code for o in c.outputs)
    assert pngs >= 28, pngs

    tex_path = ROOT / 'Exercício_Aula5.tex'
    tex = tex_path.read_text(encoding='utf8')
    figures = re.findall(r'\\detokenize\{(Figuras_Aula5/[^}]+)\}', tex)
    assert len(figures) == 27, len(figures)
    assert all((ROOT / figure).is_file() for figure in figures)
    labels = re.findall(r'\\label\{([^}]+)\}', tex)
    assert len(labels) == len(set(labels)), 'Duplicate LaTeX labels'
    stack = []
    for operation, environment in re.findall(r'\\(begin|end)\{([^}]+)\}', tex):
        if operation == 'begin':
            stack.append(environment)
        else:
            assert stack and stack.pop() == environment, environment
    assert not stack, stack

    pdf_path = ROOT / 'output/pdf/Exercicio_Aula5.pdf'
    pdf = fitz.open(pdf_path)
    assert len(pdf) >= 25
    outside = []
    for i, page in enumerate(pdf):
        for x0, y0, x1, y1, *_ in page.get_text('blocks'):
            if x0 < 0 or y0 < 0 or x1 > page.rect.width + 0.1 or y1 > page.rect.height + 0.1:
                outside.append(i + 1)
    assert not outside, outside
    full_text = '\n'.join(page.get_text() for page in pdf)
    for expected in ['Adriely Teixeira de Paula', 'Betina Zynger Capaverde',
                     'Emilio Gaudeda Junior', 'DE rand1bin', 'Optuna']:
        assert expected in full_text, expected
    audit = json.loads((ROOT / 'results/independent-audit.json').read_text(encoding='utf8'))
    assert audit['status'] == 'passed'
    output = {
        'status': 'passed', 'notebook_code_cells': len(code),
        'notebook_error_outputs': len(errors), 'notebook_embedded_pngs': pngs,
        'tex_referenced_figures': len(figures), 'tex_environments_balanced': True,
        'tex_compilation': 'not verified; requires Overleaf access',
        'pdf_pages': len(pdf), 'pdf_text_outside_page': outside,
        'independent_model_audit': 'passed',
        'sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in [notebook_path, tex_path, pdf_path, ROOT / 'experiment.py']},
    }
    (ROOT / 'delivery-validation.json').write_text(json.dumps(output, indent=2), encoding='utf8')
    print(json.dumps(output, ensure_ascii=False))


if __name__ == '__main__':
    main()
