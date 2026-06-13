# 🏁 Project Moonshot: Tape-Out Signoff Report

Physical verification and synthesis metrics from the SkyWater 130nm OpenLane EDA pipeline.

> **Scope:** This report covers the hardened design — the Efabless Caravel `user_project_wrapper` and its digital Wishbone interface. This is an **interface feasibility / PDN-stress vehicle**, *not* the CIM accelerator itself. The analog compute macro is a behavioral/SPICE model tied off in the synthesizable RTL; the synthesizable CIM compute datapath is future work. All figures below are pulled from `open_silicon/openlane/runs/moonshot_physical_build/reports/metrics.csv` and the signoff reports.

## 📊 Physical Scale
* **Synthesized logic cells:** `244`  ← the actual design (Wishbone interface)
* **Decap / well-tap / fill cells:** `2,903,370`  ← die-population cells placed for density + PDN rules
* **Total cells in GDS:** `2,903,614`
* **Logic utilization:** `1.8%`  *(intentional — the die is deliberately oversized to reserve area for the analog macro and to stress the Power Delivery Network)*
* **Die Area:** `10.28 mm²` (2920 × 3520 µm)
* **Total Routing Wire Length:** `46,613 µm`
* **Total Vias (Layer Connections):** `983`

> **Why "2.9M cells" is not design complexity:** only 244 cells are synthesized logic. The remaining ~2.9M are decoupling-capacitor, well-tap, and fill cells that OpenLane places to satisfy density and PDN rules across a 1.8%-utilized die. The big number reflects *die population*, not compute. (Consistency check: 983 vias and 46,613 µm of wire are correct for a 244-cell design — a genuine multi-million-cell design would have orders of magnitude more.)

## ⏳ Build-Host Resources
* **Peak Memory (RAM):** ~10 GB during Magic SPICE extraction
  *(driven by the oversized die + over-provisioned PDN forcing dense geometry calculations, not by design size)*

## 🛡️ Verification & Signoff *(verified)*
* **LVS Total Errors:** `0`  *("no net, device, pin, or property mismatches")*
* **Magic DRC Violations:** `0`
* **Antenna Violations:** `0`  *(pin and net)*

## ⚡ Timing & Power *(verified)*
* **Clock Target:** `10.0 ns` (100 MHz)
* **WNS / TNS:** `0.0 / 0.0 ns`  → meets timing
* **Worst Setup Slack:** `+1.33 ns` @ 100 MHz
* **Worst Hold Slack:** `+0.25 ns`
* **Internal Power (Typical):** `9.92e-05 µW`
* **Switching Power (Typical):** `1.75e-04 µW`
* **Leakage Power (Typical):** `8.02e-06 µW`

> Power is sub-µW because the hardened logic is a 244-cell interface, not a compute workload. These numbers will rise substantially once the synthesizable CIM datapath replaces the interface stub.

## 🧬 Conclusion
The Caravel interface vehicle was successfully hardened on the SkyWater 130nm process node and passes all signoff checks (LVS / Magic DRC / antenna = 0) with positive timing slack. The geometry is compliant with SkyWater 130nm photolithography rules, and the over-provisioned PDN is in place as a forward-looking countermeasure for the analog macro that will occupy the reserved die area. The next milestone is replacing the interface stub with a synthesizable CIM compute datapath so the logic-cell count reflects real MACs.
