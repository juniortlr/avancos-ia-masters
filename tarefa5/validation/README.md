# Validação da adaptação Colab

`colab_linux/` contém a execução completa do notebook Colab em um kernel Linux local via nbclient. São 61 células de código, 28 imagens incorporadas e nenhum erro. O hash registrado corresponde ao arquivo publicado. O teste exercitou o download do commit GitHub, a instalação isolada, a verificação e reconstrução dos resultados e a exportação.

`linux_smoke/` contém um teste focalizado novo, com duas CPUs, dos controles, baseline, Optuna, Ray/ASHA e Optuna em metade do treino. Não é uma repetição da suíte de 15 métodos nem uma atualização do ranking científico original. Seus scores e tempos pertencem ao ambiente Linux de validação.

Durante a primeira integração, o subprocesso herdou `MPLBACKEND=module://matplotlib_inline.backend_inline` do kernel, indisponível no venv científico. A adaptação passou a definir `MPLBACKEND=Agg` e remover `PYTHONPATH`/`PYTHONHOME` herdados. A execução integral subsequente passou. A preparação também suporta falha de `venv/ensurepip` por meio de Python 3.12 provisionado com uv e mantém caminhos curtos para os sockets locais do Ray.

Nenhum dado, modelo, score, tempo ou código do experimento original foi sobrescrito. Estes testes não afirmam execução no Colab hospedado: a ferramenta de navegador recusou acesso ao serviço. O usuário pode abrir o launcher pelo botão Colab do README e executar ambos os modos.
