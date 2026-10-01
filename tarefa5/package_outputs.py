"""Package completed, auditable outputs; preserve experiment and source files."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT=Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    required=[ROOT/'Exercício_Aula5.tex',ROOT/'Aula05_Tarefa5_Resultados.ipynb',
              ROOT/'output/pdf/Exercicio_Aula5.pdf',ROOT/'results/independent-audit.json',
              ROOT/'results/analysis.json',ROOT/'requirements-lock.txt']
    for path in required:
        if not path.is_file():
            raise FileNotFoundError(path)
    audit=json.loads((ROOT/'results/independent-audit.json').read_text(encoding='utf8'))
    assert audit['status']=='passed'
    build=json.loads((ROOT/'latex-build-manifest.json').read_text(encoding='utf8'))
    delivery=ROOT/'entrega'
    delivery.mkdir(exist_ok=True)
    overleaf=[ROOT/'Exercício_Aula5.tex']+sorted((ROOT/'Figuras_Aula5').glob('*.png'))
    with zipfile.ZipFile(delivery/'Aula05_Overleaf.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for path in overleaf:
            archive.write(path,path.relative_to(ROOT).as_posix())
    skip={'entrega','overleaf_original','__pycache__','tmp','ray-storage','.ipynb_checkpoints','.mplcache'}
    sources=[]
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file() or any(part in skip for part in path.relative_to(ROOT).parts):
            continue
        if path.suffix=='.pyc' or path.name=='notebook_source.txt':
            continue
        sources.append(path)
    manifest={'primary_outputs':[{ 'path':str(p.relative_to(ROOT)).replace('\\','/'),
                'bytes':p.stat().st_size,'sha256':sha(p)} for p in required[:3]],
              'overleaf_updated':build.get('overleaf_updated',False),
              'browser_access':'blocked; user supplies the Overleaf PDF download',
              'pdf_renderer':build['pdf_export'],
              'framework_commit':'f68892c8b7adba358b8aa437eec00a89fe88d340',
              'included_files':[{ 'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in sources]}
    mp=delivery/'delivery-manifest.json'
    mp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
    with zipfile.ZipFile(delivery/'Aula05_Reprodutivel.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for path in sources:
            archive.write(path,'tarefa5/'+path.relative_to(ROOT).as_posix())
        archive.write(mp,'tarefa5/delivery-manifest.json')
        vendor=ROOT.parent/'vendor/rnd-superpowers'
        for path in sorted(vendor.rglob('*')):
            if path.is_file():
                archive.write(path,'vendor/rnd-superpowers/'+path.relative_to(vendor).as_posix())
    print(json.dumps({'archives':[{ 'file':p.name,'bytes':p.stat().st_size} for p in delivery.glob('*.zip')]}))

if __name__=='__main__':
    main()
