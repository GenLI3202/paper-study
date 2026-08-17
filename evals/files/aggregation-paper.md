# Synthetic paper fixture: Aggregating Distributed BESS and PV

> This is a synthetic evaluation source, not a published paper.

<!-- Page 1 -->

## Abstract

A virtual power plant aggregates distributed PV and BESS to provide energy and frequency services. We compare centralized and distributed coordination. Centralized optimization gives a global objective but requires full telemetry; distributed coordination exchanges local schedules and dual variables while preserving local constraints.

## 1. Introduction

The paper asks how independently owned PV+BESS sites can present one grid-facing schedule. Section 2 defines the aggregation objective, Section 3 compares architectures, Section 4 reports a numerical case, and Appendix A summarizes battery chemistries.

<!-- Page 2 -->

## 2. Aggregation objective

The aggregator minimizes

`J = energy_cost + imbalance_penalty + reserve_shortfall_penalty` (Eq. 1)

subject to one aggregate power-balance constraint and each site's local power and SOC limits. Figure 1 shows site forecasts flowing to the aggregator and setpoints returning to sites.

**Figure 1.** Information flow between three local PV+BESS controllers and one aggregator.

<!-- Page 3 -->

## 3. Coordination architectures

### 3.1 Centralized

The aggregator receives forecasts, SOC states, and constraints from every site and solves Eq. 1 jointly. This exposes the full feasible region but creates a single communication and computation point.

### 3.2 Distributed

Each site solves a local subproblem. Sites exchange proposed aggregate power and coordination prices until the aggregate balance residual is below a tolerance. The paper calls this a distributed price-coordination method; it does not name ADMM or prove convergence.

**Table 1. Architecture comparison.** Centralized: global data required, one solve. Distributed: local data retained, iterative messages required.

<!-- Page 4 -->

## 4. Numerical case

For three synthetic sites, both architectures reach aggregate schedules within 1.5% cost difference. The distributed method uses 18 coordination rounds. These values apply only to the stated three-site case.

## Appendix A. Battery chemistry summary

A descriptive table compares LFP and NMC energy density and thermal characteristics. No chemistry parameter enters Eq. 1 or the architecture comparison.
