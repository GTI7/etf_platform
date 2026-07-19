"""Concrete gate implementations (Validation domain, Step 7 minimal increment).

Two gates: ``signal_independence`` and ``economic_rationale``. Neither
is a ``Gate`` Protocol implementation -- that Protocol, along with
``GateRunner`` and ``ValidationRegistry``, remains deferred (AD-044).
Each is a plain function taking explicit typed parameters and
returning a ``core.validation.gate_result.GateResult``.

Neither gate computes a statistic. Per AD-041, statistic computation
(IC, correlation, permutation tests, significance) belongs to
``core.statistics`` alone; these gates only compare an
already-computed value against a caller-supplied frozen criterion.
Neither imports ``core.statistics`` as a result.
"""
