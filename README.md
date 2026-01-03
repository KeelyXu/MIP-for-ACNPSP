

# MIP Models (MIP1 & MIP2) for Air Cargo Network Planning and Scheduling problem (ACNPSP)

![Date](https://img.shields.io/badge/Completion_Date-January_2025-blue.svg)

## Overview

This project utilizes **a two-stage Mixed Integer Programming (MIP)** approach to solve air cargo logistics problems. The process is divided into a macro-level network design phase (MIP1) and a micro-level flight timetabling phase (MIP2). For the details of the models, see  [MIP models.pdf](assets\MIP models.pdf) 

------

## Model 1: Network Design & Flow Planning (MIP1)

**Context:** The strategic planning phase focusing on cost reduction and capacity allocation.

### Key Decision Variables

- **Hub Location ($y_i$):** Determines whether a specific city node $i$ is selected as an aviation hub ($y_i=1$) or not.
- **Aircraft Assignment ($m_{ij}^k$):** Decides the number of owned aircraft of type $k$ assigned to the route arc $(i,j)$. This includes variables distinguishing between discounted and non-discounted hub transport ($m_{0ij}^k, m_{1ij}^k$).
- **Cargo Routing ($x_{ij}^{od}$):** Determines the volume of cargo for a specific Origin-Destination (OD) pair transported across arc $(i,j)$. It handles both direct flights and multi-hub transfers.
- **Path Sequencing ($z_{ij}^{od}, s_i^{od}$):** Controls the routing path sequence to ensure logical flow and eliminate sub-tours.

### Objective

Minimize the total cost, which consists of:

1. Hub construction/setup costs.
2. Owned aircraft transportation costs (considering inter-hub discount factors $\alpha$).
3. Outsourced air freight costs.

------

## Model 2: Cargo Distribution & Flight Timetabling (MIP2)

**Context:** The tactical scheduling phase. It takes the flow and fleet results from MIP1 as fixed inputs to generate specific flight schedules.

### Inputs from MIP1

- **Total Transport Volume ($X_r^*$):** The volume assigned to specific transport flows derived from MIP1.
- **Fleet Size ($M_e^{k\*}$):** The number of aircraft of type $k$ utilized on arc $e$, as determined by MIP1.

### Key Decision Variables

- **Flight Plan Allocation ($x_f$):** Assigns cargo volume to specific feasible flight schemes/sequences $f$.
- **Departure Timing ($y_{ea}^j$):** Determines if a specific aircraft $j$ departs at a specific discrete time $a$ on route $e$.
- **Round-Trip Sequencing ($z_j$):** Manages the order of service for aircraft operating bidirectionally (e.g., determining if the aircraft flies $i \rightarrow j$ first or $j \rightarrow i$ first) to ensure time feasibility.

### Objective

Minimize the total cargo retention time (weighted by cargo mass) within the network to ensure efficiency and timeliness.

------

## Usage Note

- **Sequential Execution:** MIP1 must be solved first. The outputs regarding deployed fleet size ($m_{ij}^k$) and route flows ($x_{ij}^{od}$) become hard constraints/parameters for MIP2.
- **Assumptions:**
  - MIP1 assumes owned aircraft operate on a specific route with one round-trip per cycle.
  - MIP2 assumes discrete feasible departure times.

------

## Reference

1. Zhang, C., Xie, F., Huang, K., Wu, T., & Liang, Z. (2017). MIP models and a hybrid method for the capacitated air-cargo network planning and scheduling problems. *Transportation Research Part E: Logistics and Transportation Review*, *103*, 158-173.
2. Zheng, H., Sun, H., Zhu, S., Kang, L., & Wu, J. (2023). Air cargo network planning and scheduling problem with minimum stay time: A matrix-based ALNS heuristic. *Transportation Research Part C: Emerging Technologies*, *156*, 104307.

