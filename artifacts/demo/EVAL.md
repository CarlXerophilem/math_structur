# Demo evaluation

- Adaptive first failure: step **2**.
- Random baseline median first failure over 20 seeds: step **2**.
- Adaptive statuses: `['equivalent', 'mismatch', 'mismatch', 'mismatch', 'undefined']`.
- SymPy real-domain baseline: `{'status': 'computed', 'compiled_domain': 'Interval.open(0, oo)', 'reference_domain': 'Interval.open(0, oo)', 'note': 'real continuity baseline; it does not compare complex principal-branch values'}`.
- Finite-map positive: `proved_finite`.
- Finite-map counterexample: `refuted`.
- Finite-map closure failure: `invalid`.
- Lean: `partial_formalization` — local obligation compiles; repository EML reconstruction remains incomplete because reconstruct_ln uses sorry.

## Verdict

The minimum environment passes its technical gate: feedback changes the next probe, the known negative-real-axis branch mismatch is reproduced, zero remains undefined, and finite-domain closure failures are separated from equation counterexamples. The adaptive policy is **not better than the random median** in this tiny pool if `2 >= 2`; no superiority claim is permitted.
