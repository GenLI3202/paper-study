# Synthetic paper fixture: Aging-Aware BESS Operation Review

> This is a synthetic evaluation source, not a published paper.

<!-- Page 1 -->

## Abstract

This review groups battery-aging costs used in operational optimization into throughput, cycle-depth, and state-dependent models.

## 1. Scope

The review asks how battery degradation can be represented in scheduling without embedding a full electrochemical model.

<!-- Page 2 -->

## 2. Operational aging costs

### 2.1 Throughput model

`C_deg = c_E · Σ_t |p_t| Δt` (Eq. 2)

The model is linear and tractable but does not distinguish shallow from deep cycles.

### 2.2 Cycle-depth model

Cycle counting assigns a nonlinear cost to each identified depth of discharge. It captures cycle severity but couples decisions across time.

### 2.3 State-dependent model

A stress multiplier depends on SOC and temperature. Evidence summarized in the review covers cell tests between 20% and 90% SOC; extrapolation outside that range is not validated.

<!-- Page 3 -->

## 3. Scheduling implications

Adding degradation cost can conflict with reserve and arbitrage revenue. The review does not study multi-owner aggregation, privacy, or how degradation costs should be allocated among sites.
