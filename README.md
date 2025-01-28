# 🚑 Heuristics and Optimization: Ambulance Allocation and Patient Transfer

This project focuses on solving two distinct problems: allocating ambulances in a parking lot under various constraints and optimizing the transfer of patients using heuristic search algorithms.

---

## 📝 Problem Overview

### Part 1: **Ambulance Allocation**
- **Goal**: Allocate ambulances to parking spaces while respecting constraints like:
  - Electric connections required for specific ambulances.
  - No ambulance blocking emergency vehicles.
  - Adjacency and space restrictions.
- **Approach**: Modeled as a **Constraint Satisfaction Problem (CSP)** using the Python `constraint` library.

### Part 2: **Patient Transfer Optimization**
- **Goal**: Minimize the time and energy required to transport patients between homes, care centers, and parking lots.
- **Approach**: Implemented with heuristic search algorithms, specifically **A\***, utilizing multiple heuristic functions to evaluate performance.

---

## 🛠️ Features

- **Ambulance Allocation (Part 1)**:
  - Define constraints and allocate parking spaces.
  - Validate scenarios with Python `constraint`.
  - Includes test cases for extreme and edge scenarios.

- **Patient Transfer Optimization (Part 2)**:
  - Implemented the **A\*** algorithm.
  - Designed and analyzed four different heuristic models:
    1. Basic relaxed constraints.
    2. Fully informed heuristics.
    3. Priority-based heuristics.
    4. Relaxed capacity constraints.

---

## 📂 Project Structure
Redactar
- **`parte 1/`**: Implementation of Ambulance Alocation.
  - **`CSP-tests/`**: Implementation of the diferent scenarios for the problem
  - **`CSP-calls.sh`**: Implementation of the A\* algorithm for patient transfer optimization.
  - **`CSPParking.py`**: Implementation of the A\* algorithm for patient transfer optimization.
- **`parte 2/`**: Contains heuristic functions and their evaluations.
  - **`ASTAR-tests/`**: 
  - **`ASTAR-calls.sh`**:
  - **`ASTARTraslados.py`**:

---

## 🚀 How to Run

### Part 1: CSP - Ambulance Allocation
To test ambulance allocation scenarios, execute the provided script:
```bash
bash csp/CSP-calls.sh
