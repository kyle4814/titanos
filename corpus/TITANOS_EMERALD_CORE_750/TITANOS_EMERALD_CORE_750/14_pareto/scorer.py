def score(value, unlock, evidence, risk_reduction, complexity):
    return (0.30*value + 0.25*unlock + 0.20*evidence +
            0.15*risk_reduction - 0.10*complexity)
