<div align="center">

# 🚀 Project Moonshot
### The Datacenter-Class Analog CIM Architecture

</div>

---

## 🧭 Vision

To take Analog Compute-in-Memory out of the low-power Edge AI space and move it into the high-performance, datacenter-tier arena dominated by NVIDIA, we have to fundamentally change the physics, packaging, and software ecosystem.

Project Moonshot executes on three major vectors:

1. **The Silicon Leap (Advanced Nodes & NVM):** Transitioning from 130nm CMOS charge-sharing to emerging non-volatile memory (NVM) technologies like multi-level RRAM or MRAM integrated directly into a TSMC 22nm or 3nm CMOS back-end-of-line (BEOL).
2. **The Packaging Revolution (Chiplets & 2.5D):** Abandoning the monolithic SoC approach for Advanced Packaging. Analog CIM macros are designed as individual "Chiplets" mounted alongside advanced digital orchestrators and massive High-Bandwidth Memory (HBM3e) stacks on a silicon interposer (e.g. CoWoS).
3. **The Software Wall (The MLIR Compiler):** NVIDIA's moat isn't just silicon; it's CUDA and TensorRT. Project Moonshot focuses on building an LLVM-based compiler stack (MLIR) that takes standard PyTorch code, chunks matrix multiplications, and maps them to physical analog chiplets while automatically applying dynamic body-bias calibrations under the hood.

---

## 🗂️ Project Structure

This repository is primarily focused on **The Software Wall** — bridging the gap between high-level machine learning frameworks and the physical analog tiles.

```text
Project-Moonshot/
├── compiler/       # The MLIR-based compiler stack
│   ├── mlir-dialects/  # Custom MLIR dialects for Analog CIM operations
│   └── passes/         # Transformation passes for matmul chunking and mapping
├── frontend/       # High-level framework integration
│   └── pytorch_integration.py # Mock PyTorch bindings to intercept standard layers
├── simulator/      # Architectural Simulators
│   └── chiplet_interposer_sim.py # Roofline simulator modeling 2.5D HBM/CoWoS bottlenecks
└── README.md       # This file
```

---

## 🛠️ Quick Start

**Run the 2.5D Interposer Architectural Simulator:**
```bash
python simulator/chiplet_interposer_sim.py
```

**Test the PyTorch Frontend Interception:**
```bash
python frontend/pytorch_integration.py
```
