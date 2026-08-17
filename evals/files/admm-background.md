# Synthetic background fixture: ADMM coordination

> This is a synthetic evaluation background source, not part of the aggregation paper and not a published citation.

<!-- Page 1 -->

The alternating direction method of multipliers (ADMM) is one possible coordination method for a separable convex optimization problem with a coupling or consensus constraint. A typical iteration alternates local primal-variable updates with a shared consensus update and a dual-variable update.

For distributed energy coordination, a site can retain its local objective and constraints while exchanging coupling quantities with a coordinator. This does not by itself prove convergence for a particular nonconvex battery model. Convergence claims depend on the mathematical assumptions, update rules, and stopping criteria of the implementation being studied.

A comparison with generic distributed price coordination should therefore distinguish:

- what variables and messages are exchanged;
- whether an augmented-Lagrangian penalty is present;
- what convexity and feasibility assumptions hold;
- how residuals and termination are defined.
