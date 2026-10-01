# Avanços em Inteligência Artificial — PPGEE/UFPR

Exercícios e resultados da disciplina EELT7025. Integrantes: **Adriely Teixeira de Paula, Betina Zynger Capaverde e Emilio Gaudeda Junior**.

[![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/juniortlr/avancos-ia-masters/blob/main/tarefa5/Aula05_Tarefa5_Colab.ipynb)

## Executar no Google Colab

Abra o notebook pelo botão acima e escolha **Ambiente de execução → Executar tudo**, com runtime CPU. Não é necessário enviar arquivos: o notebook baixa automaticamente o snapshot publicado, instala as dependências em um ambiente Python 3.12 isolado e mostra as respostas aos exercícios.

- `analise_arquivada` é o padrão: verifica o snapshot e reconstrói os resultados, tabelas e gráficos sem refazer as buscas.
- `experimento_completo` refaz todos os métodos, controles, comparação amostral e robustez. Os resultados são gravados em uma pasta nova e podem ser baixados ao final.

O notebook [Aula05_Tarefa5_Colab.ipynb](tarefa5/Aula05_Tarefa5_Colab.ipynb) fixa o commit dos materiais arquivados e registra o ambiente de cada execução. O paralelismo se adapta à CPU disponível. Os tempos da execução original não são apresentados como tempos do Colab. Recursos e duração de sessões podem variar, conforme a [documentação oficial do Colab](https://research.google.com/colaboratory/faq.html).

**Validação realizada:** a versão publicada executou 61/61 células em Linux, gerando 28 imagens sem erros. O teste usou kernel Python 3.14 e o Python 3.12 isolado instalado pelo próprio notebook. Um teste adicional com duas CPUs completou baseline, controles Dummy/Ridge, Optuna40, Ray40/ASHA e Optuna com metade do treino; o Ray concluiu 22 trials e podou 18. Evidências: [notebook executado em Linux](tarefa5/validation/colab_linux/analysis_executed.ipynb), [validação das células](tarefa5/validation/colab_linux/validation.json) e [teste de otimização](tarefa5/validation/linux_smoke/linux-smoke-validation.json). Esses testes foram locais em Linux/WSL; não se alega execução em uma sessão hospedada do Google Colab. A suíte original completa permanece separada dos testes de portabilidade.

## Tarefa 5 — otimização de hiperparâmetros

Comparação de estratégias de otimização do `GradientBoostingRegressor` no dataset **Concrete Compressive Strength (UCI 165)**. O relatório cobre os dois exercícios e os itens 1–10 do enunciado, incluindo GP manual, cinco bibliotecas de otimização Bayesiana, GA, DE, PSO e análise de robustez.

| Material | Arquivo |
|---|---|
| Notebook com os resultados executados | [Aula05_Tarefa5_Resultados.ipynb](tarefa5/Aula05_Tarefa5_Resultados.ipynb) |
| Relatório de 38 páginas | [Exercicio_Aula5.pdf](tarefa5/output/pdf/Exercicio_Aula5.pdf) |
| Fonte LaTeX | [Exercício_Aula5.tex](tarefa5/Exercício_Aula5.tex) |
| Figuras para o Overleaf | [Figuras_Aula5](tarefa5/Figuras_Aula5) |
| Implementação de todos os experimentos | [experiment.py](tarefa5/experiment.py) |
| Análise e gráficos | [plot_results.py](tarefa5/plot_results.py) |
| Dados, split e contrato | [data](tarefa5/data) |
| Trials, previsões, modelos e métricas | [results](tarefa5/results) |
| Protocolo e orçamento prospectivos | [study-protocol.md](tarefa5/study-protocol.md), [search-budget.json](tarefa5/search-budget.json) |
| Enunciado original fornecido | [Aula05_Enunciado.ipynb](enunciados/Aula05_Enunciado.ipynb) |

Os 15 métodos/variantes totalizaram 2.281 avaliações na comparação principal. A auditoria passou em 280 verificações aritméticas e de integridade; CV, previsões e métricas dos 15 modelos também foram recalculados separadamente. O notebook arquivado executou 71 células de código, sem erros, e contém 28 figuras incorporadas.

| Referência da execução arquivada | RMSE (MPa) |
|---|---:|
| Baseline no teste | 5,603850 |
| Menor CV: PSO, inércia 0,9 | 4,527704 |
| Menor erro descritivo no teste: DE rand1bin | 4,413513 |

A escolha por CV e o vencedor descritivo do teste são distintos. O holdout é fixo e contém algumas composições também presentes no treino com respostas diferentes; não comprova generalização para receitas inéditas. Cinco seeds avaliam aleatoriedade condicional ao split, não cinco datasets independentes. Os métodos têm orçamentos e resoluções diferentes. Consulte o relatório antes de generalizar o ranking.

## Reprodução local

O experimento original usou Python 3.12. As versões instaladas estão em [requirements-lock.txt](tarefa5/requirements-lock.txt). Os tempos registrados pertencem à máquina original; uma nova execução deve manter seus próprios tempos e resultados.

```bash
python -m venv .venv
# Ative o ambiente virtual conforme seu sistema.
python -m pip install -r tarefa5/requirements-lock.txt
python tarefa5/experiment.py verify
python tarefa5/audit_saved_outputs.py --require-all
python tarefa5/plot_results.py
```

Para repetir as buscas, siga [LEIA-ME.txt](tarefa5/LEIA-ME.txt) e use uma cópia separada dos artefatos. Os dados preservados permitem reconstruir a análise sem depender de uma nova consulta à UCI. Logs temporários do Ray, caches, ambientes virtuais e arquivos intermediários de renderização não são versionados.

## Overleaf e aulas anteriores

Para a Aula 5, adicione `Exercício_Aula5.tex` na raiz do projeto e a pasta `Figuras_Aula5` ao lado dele; selecione essa fonte como documento principal. O PDF disponibilizado foi exportado de blocos compartilhados com o LaTeX usando ReportLab. A compilação no Overleaf ainda não foi verificada; o acesso automatizado ao projeto permaneceu bloqueado por uma preferência salva do navegador.

As fontes e figuras das [aulas 1–4](referencias/overleaf_aulas_01_a_04) são cópias do projeto usado como referência. Foram preservadas como recebidas, sem alegar reexecução ou validação dos seus experimentos. Não foram fornecidos notebooks executáveis dessas quatro aulas nesta sessão.

## Fontes e atribuições

- Dados: I-Cheng Yeh, [Concrete Compressive Strength, UCI 165](https://doi.org/10.24432/C5PK67), CC BY 4.0. A remoção de 25 duplicatas completas e a divisão de 1.005 linhas em 804/201 são registradas no contrato de dados.
- Metodologia: [juniortlr/rnd-superpowers, commit f68892c8b7adba358b8aa437eec00a89fe88d340](https://github.com/juniortlr/rnd-superpowers/commit/f68892c8b7adba358b8aa437eec00a89fe88d340). O snapshot em [vendor](vendor/rnd-superpowers) contém os 50 arquivos centrais usados, com hashes Git verificados e manifesto. Trata-se de procedimentos de pesquisa, não de um motor de HPO.
- O notebook em `enunciados/` é material didático fornecido, com autoria e conteúdo originais preservados. As referências bibliográficas completas constam do relatório.

Este repositório não atribui uma licença global aos materiais de terceiros. Os termos e atribuições de cada fonte continuam aplicáveis. O [manifesto de publicação](publication-manifest.json) registra os arquivos e seus hashes.
