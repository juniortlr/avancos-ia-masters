# Protocolo prospectivo — Tarefa 5, versão 1

Registrado em 30/09/2026, 20:29 (America/Sao_Paulo), antes da execução dos experimentos. Este é um protocolo local, não um registro público. Nenhum resultado de HPO ou avaliação desta execução havia sido observado ao fixar estas escolhas. O enunciado, o código de exemplo da aula e trabalhos anteriores foram consultados; isso não constitui evidência do desempenho dos métodos nesta execução.

## Problema e objetivo

Comparar o desempenho preditivo e o custo computacional de estratégias de otimização de hiperparâmetros (HPO) de `GradientBoostingRegressor` na resistência à compressão do concreto. A referência exigida é o modelo com os padrões do scikit-learn, exceto `random_state=42`. A hipótese de trabalho é que o HPO pode diminuir o RMSE de validação e de teste em relação a essa referência, com custos diferentes. Uma piora no teste, ganhos muito pequenos ou custo elevado desafiam a recomendação de otimizar. Nenhum ganho mínimo de relevância industrial é assumido: o contexto não fornece tolerância de engenharia ou custo monetário do erro.

O estudo é uma comparação computacional didática, exploratória, em um único dataset e um holdout. Não estima um efeito causal do otimizador nem demonstra superioridade universal. Os diferentes budgets obrigatórios e resoluções dos espaços confundem comparações estritamente atribuíveis ao algoritmo.

## Dados e unidade

Fonte: UCI Machine Learning Repository, Concrete Compressive Strength, id=165, obtido por `ucimlrepo.fetch_ucirepo(id=165)`. Usar o conjunto integral disponibilizado, com 8 preditores numéricos e alvo em MPa. Uma linha é uma observação de composição/idade e resistência do concreto, não um instante de série temporal. A ausência de identificadores de lote impede garantir independência entre misturas relacionadas; não se alegará generalização temporal, entre laboratórios ou para lotes desconhecidos.

Inspecionar shape, dtypes, proporção ausente, estatísticas e duplicatas antes do ajuste. Remover duplicatas exatas da linha completa (X e y), preservando uma cópia; documentar contagem e efeito no tamanho. Não remover observações por erro do modelo, nem tratar zero como ausente. Se houver alvo ausente, a linha é inelegível; registrar a contagem. Mediana para ausentes em X dentro do pipeline. A regra é preventiva caso não existam ausentes. Salvar dados locais e SHA-256, metadados, ordem/identificação das linhas e split para rastreabilidade.

## Contrato de avaliação

Após a limpeza determinística, split de 80% treino e 20% teste, `random_state=42`. O conjunto de teste é reservado ao desempenho final de cada configuração escolhida; nenhuma configuração é proposta com seu score. Validação interna: `KFold(n_splits=5, shuffle=True, random_state=42)`, os mesmos índices em todos os métodos principais. `SimpleImputer(strategy='median')`, `StandardScaler` e GBR formam um único pipeline ajustado em cada fold. O scaler é exigido pelo exercício, embora árvores não necessitem padronização; o alvo permanece em MPa.

Métrica primária da busca: média do RMSE dos cinco folds, minimizada (conversão explícita do score negativo das APIs sklearn). Reportar RMSE, MAE e R² no holdout; RMSE/MAE em MPa. O RMSE médio de folds não é o RMSE de todas as previsões out-of-fold agrupadas. Nenhum teste pareado entre otimizadores será interpretado como confirmatório; não há múltiplos datasets independentes nem uma amostragem de replicações suficiente para tal inferência.

Registrar tempo de busca (inclusive todo fit CV e overhead do método), refit no treino integral e soma; baseline: CV mais refit para tempo total comparável, e tempo de fit separado como solicitado. Não incluir instalação, download, EDA e gráficos. Usar CPU local, modelos sequenciais e mesmo paralelismo; registrar versões e hardware. Os tempos de parede refletem esta execução e interferência do sistema, sem promessa de benchmark de hardware.

## Espaço de busca fixo

Hiperparâmetros livres: learning_rate de 0,03 a 0,20 (escala log); subsample de 0,60 a 1,00; n_estimators inteiro de 50 a 200. Demais parâmetros ficam nos defaults sklearn, com seed controlada. Grid avalia o produto `[0.03,0.10,0.20] × [0.60,0.80,1.00] × [50,100,150,200]` (36 candidatos); Random escolhe 30 candidatos sem reposição dessa mesma grade com seed 42.

Os demais métodos usam os mesmos limites, mas resoluções contínuas/inteiras apropriadas à biblioteca. Isso é necessário para conciliar as exigências de GP contínuo e `hp.loguniform` com a grade, e fica explicitamente declarado. Não são o mesmo conjunto de candidatos. Random discreto não pode superar estritamente o mínimo CV da grade exaustiva sob folds e modelo idênticos; poderá igualá-lo antes. As curvas registram a melhor observação acumulada na ordem efetiva dos candidatos, não uma evolução temporal intrínseca da grade.

GP manual: dois contínuos (learning_rate em log e subsample), n_estimators fixado prospectivamente em 100. Matérn ν=2,5, cinco pontos iniciais e dez aquisições Expected Improvement (15 avaliações). Cada posterior e EI serão registrados antes de avaliar o próximo candidato. Para exibir média ±2σ num problema 2D, usar corte pelo subsample do candidato e declarar o corte; observações fora dele são contexto projetado, não valores observados da curva. Mapas 2D podem complementar. Essa demonstração não explora o espaço completo.

Bibliotecas: BayesSearchCV com GP, EI e Matérn 5/2; BayesianOptimization GP-UCB, κ=2,576; Optuna TPE; Hyperopt TPE com LR loguniform; Ray Tune OptunaSearch e ASHA. Cada uma inicia 40 trials conforme o enunciado. ASHA deve receber RMSE CV em estágios crescentes reais de recurso; trials interrompidos não equivalem a avaliações completas. A implementação exata do recurso e codificação será documentada antes da execução, em aditamento.

GA: DEAP, codificação inteira documentada, população 20, 15 gerações, probabilidade de crossover 0,7 e mutação 0,25; contabilizar apenas chamadas fitness realizadas, sem estimar cegamente população×gerações. DE: best1bin e rand1bin, maxiter=15, popsize=10 multiplicador da dimensão (30 indivíduos), mutation=(0.5,1.0), recombination=0.7, polish=False. Registrar término e nfev real. PSO: 20 partículas, inicialização mais 15 atualizações, w=0,7, c1=c2=1,5; repetir w=0,4 e 0,9; registrar gbest e média do fitness do enxame corrente, não média pbest.

## Análises prospectivas

1. EDA (histograma do alvo, correlação e dispersão), diagnósticos do baseline, convergência Grid/Random, heatmap com terceiro HP no ótimo e Spearman (RMSE positivo: correlação negativa associa valores maiores a erro menor).
2. Posteriores e EI das dez iterações do GP; convergência das cinco bibliotecas; fitness/diversidade GA, comparação DE e comparação das três inércias PSO.
3. Tabela completa e variantes; radar orientando todos os eixos para maior=melhor por min-max dentro do conjunto exibido; scatter e Pareto minimizando RMSE teste e tempo total, preservando empates.
4. Vencedor descritivo por menor RMSE teste, exigido pelo enunciado: real versus previsto, resíduos y−ŷ, Shapiro–Wilk e importância impura das features, com suas limitações. Shapiro é diagnóstico exploratório; rejeitar normalidade não invalida automaticamente uma regressão.
5. Importâncias de hiperparâmetros Optuna pelo avaliador disponibilizado na biblioteca. Comparar HPO no treino integral com HPO em subamostra aleatória de 50% do treino (mesmo teste reservado, mesmas regras de folds, espaço e budget), explicitamente separada da comparação principal. Não afirmar comparação amostra/integral sem executá-la.
6. Robustez: repetir o procedimento HPO inteiro do vencedor descritivo por teste com seeds [0,7,21,42,99]; manter o holdout principal fixo. Variar seed do otimizador e estimador, mantendo folds fixos para atribuir a variação à aleatoriedade computacional. Informar média e desvio padrão amostral (ddof=1) do Test RMSE. As seeds não são cinco datasets e não fornecem IC rigoroso de generalização. A execução seed=42 já concluída pode ser reutilizada, com essa reutilização declarada.
7. Eficiência = `((RMSE_baseline−RMSE_método)/RMSE_baseline)/(tempo_total_método−tempo_total_baseline)`. Baseline é indefinido. Denominador ≤0 será marcado como não definido e interpretado separadamente; não haverá divisão silenciosa nem substituição por epsilon.

## Seleção, orçamento e parada

A escolha metodológica principal é o menor CV RMSE entre configurações retornadas pelos métodos; o vencedor por teste será descrito para cumprir os itens 9.4 e 10.2. Selecioná-lo entre muitos métodos expõe o teste ao desenvolvimento: os resultados finais e a recomendação serão exploratórios, sem retuning após olhar o holdout e sem alegar teste confirmatório intacto.

Orçamento completo em `search-budget.json`. Um ciclo executado de problema → baseline → comparação → sensibilidade (inércia, estratégia, tamanho de treino e seeds) → revisão. Encerrar cada método no budget especificado; falhas não são resultados nulos ou valores sintéticos. Não repetir buscas para obter melhor resultado. Corrigir falhas de implementação registrando causa, código e nova execução; preservar logs. Meta de parede operacional de seis horas, sem desligamento forçado implícito; se ultrapassar, registrar desvio e estado. Apenas CPU local; sem serviços pagos. Comparações têm budgets diferentes por exigência didática e serão discutidas como qualidade versus custo.

## Evidências e revisão

Salvar código executável, ambiente, dados/manifesto, folds, cada trial e seu status, scores CV, parâmetros, tempos, previsões, métricas, figuras e artefatos de entrega. Nunca preencher números antes da execução. Protocolos e resultados terão arquivos distintos. Revisão de integridade/aderência e inspeção visual das figuras precedem a entrega; revisão assistida por IA não equivale a endosso humano.

Amendment log: versão 1 criada antes da execução; detalhes técnicos pendentes (schema, estágio ASHA e codificação GA) serão acrescentados com data e indicação de exposição aos resultados. Alterações após resultados serão rotuladas como exploratórias.

### Aditamento técnico 1 — 30/09/2026, 20:34 (antes dos scores)

O engine foi inspecionado antes de executar resultados: uma busca por vez, com os cinco folds em paralelo (`--jobs 5`) e cada estimador limitado a uma thread. Isso mantém a mesma oportunidade de CPU entre métodos, sem combinar métodos simultâneos. O aquecimento de workers, se feito, é separado e registrado; o ajuste/transformação de cada modelo continua contabilizado. Além da referência GBR obrigatória, DummyRegressor e Ridge podem ser reportados como verificações auxiliares da dificuldade da tarefa, fora da classificação principal de otimizadores.

GA usa genes inteiros `[0..1000, 0..1000, 50..200]`; os primeiros mapeiam, respectivamente, LR em escala log e subsample em escala linear. Diversidade GA é a proporção de genótipos distintos na população; PSO registra adicionalmente a média do desvio padrão das coordenadas normalizadas.

Ray/ASHA informa o RMSE dos cinco folds a cada fração `[0.25, 0.5, 0.75, 1.0]` do `n_estimators` proposto (arredondamento para cima), com `warm_start`; apenas trials que atingem recurso 1,0 podem ser finalistas. `time_attr=resource`, `max_t=1.0`, `grace_period=0.25`, `reduction_factor=2`. O recurso comum é fração do número de árvores de cada candidato; a quantidade absoluta de árvores varia com o HP. Registrar número de etapas e soma dos incrementos de árvores dos cinco folds. Uma chamada fit por etapa não representa retreinar todas as árvores devido a warm_start.

As análises gráficas de EDA serão no treino após o split; shape, tipos, missing e describe integral atendem ao item 1.1 sem usar o teste para escolher configurações. A robustez será executada para os vencedores por CV e por teste se forem distintos (até dois métodos); o vencedor por teste satisfaz o enunciado e o por CV esclarece a seleção adequada. Nenhum score havia sido visto ao registrar essa extensão. As seeds 42 existentes serão reutilizadas de forma explícita.
