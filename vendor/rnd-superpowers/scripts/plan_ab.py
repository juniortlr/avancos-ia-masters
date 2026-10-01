"""Approximate fixed-horizon, equal-allocation, independent binary-outcome A/B sample size.

Not valid as-is for cluster randomization, sequential testing or repeated subjects.
Planning approximation only; verify exact/simulation power for small or extreme rates.
"""
import argparse
import json
import math
from statistics import NormalDist


def plan(p0, absolute_effect, alpha=0.05, power=0.8, units_per_period=None):
    p1 = p0 + absolute_effect
    if not all(math.isfinite(x) for x in (p0, absolute_effect, alpha, power)):
        raise ValueError('inputs must be finite')
    if not (0 < p0 < 1 and 0 < p1 < 1) or absolute_effect == 0:
        raise ValueError('both rates must lie strictly between 0 and 1 and effect must be nonzero')
    if not (0 < alpha < 1 and 0.5 < power < 1):
        raise ValueError('alpha must be in (0,1), power in (0.5,1)')
    if units_per_period is not None and (not math.isfinite(units_per_period) or units_per_period <= 0):
        raise ValueError('units_per_period must be positive and finite')
    normal = NormalDist()
    average = (p0+p1)/2
    n = math.ceil(((normal.inv_cdf(1-alpha/2)*math.sqrt(2*average*(1-average)) +
                    normal.inv_cdf(power)*math.sqrt(p0*(1-p0)+p1*(1-p1))) / abs(absolute_effect))**2)
    return {'baseline': p0, 'alternative': p1, 'absolute_effect': absolute_effect,
            'alpha': alpha, 'power': power, 'n_per_arm': n, 'n_total': 2*n,
            'ideal_recruitment_periods': None if units_per_period is None else 2*n/units_per_period,
            'assumptions': ['two-sided fixed-horizon test', '1:1 allocation', 'independent subjects',
                            'normal approximation', 'no attrition, multiplicity or outcome delay included'],
            'warning': 'planning estimate; not an observed result or a clustered/sequential design'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', type=float, required=True)
    p.add_argument('--effect', type=float, required=True, help='absolute probability change, e.g. .10')
    p.add_argument('--alpha', type=float, default=.05)
    p.add_argument('--power', type=float, default=.8)
    p.add_argument('--units-per-period', type=float)
    a = p.parse_args()
    try:
        print(json.dumps(plan(a.baseline, a.effect, a.alpha, a.power, a.units_per_period), indent=2))
    except ValueError as e:
        p.error(str(e))
