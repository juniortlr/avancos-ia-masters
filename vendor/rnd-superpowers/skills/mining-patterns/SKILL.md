---
name: mining-patterns
description: "Use when: Discover clusters, segments, association rules, anomalies and frequent patterns through data mining with stability and held-out validation."
---

# Mining Patterns


## Procedure
1. Name the unit: observation, participant, sample, group or event. Choose a useful action or scientific interpretation for a discovered pattern. Read `exploring-data` first if grain or quality is unresolved.
2. Choose representation and distance deliberately. Scale numeric features within development data; encode mixed types appropriately. Remove identifier proxies, duplicated features and outcome leakage. State how long entities are observed and normalize exposure where justified.
3. Use a simple comparison: K-means for approximately spherical numeric groups; hierarchical/density methods for other geometries; PCA for linear structure; isolation or robust residual methods for anomalies. Compare at least one trivial/no-segmentation baseline.
4. Check cluster stability across entity resamples, seeds, feature sets and time periods; report cluster sizes, noise fraction and interpretable profiles. Silhouette and a attractive UMAP picture do not establish real populations. Align labels before comparing partitions.
5. For association rules, report support count, support, confidence, lift and an appropriate null. Correct for the searched family and replicate rules on later transactions. Common items alone produce high confidence.
6. Audit anomaly samples with domain experts; distinguish sensor/pipeline faults from rare operating regimes. Evaluate precision at review capacity when labels exist; unlabeled anomaly scores have no verified detection accuracy.
## Deliver
Write `pattern-catalog.csv` with discovery/validation status, stability evidence, plausible explanation and next action; save the fitted representation and reproducible configuration.
## Stop or hand off
Do not name clusters as causal mechanisms or intrinsic identities. Unstable segmentation remains exploratory. A predictive deployment needs `training-classical-ml`.
