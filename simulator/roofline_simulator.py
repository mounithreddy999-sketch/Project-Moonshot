import os
import math
import matplotlib.pyplot as plt

class ProjectMoonshotSimulator:
    def __init__(self):
        # Configuration Databases
        self.nodes = {
            "130nm Planar": {"peak_compute": 10.0, "efficiency": 2.0},       # TOPS, TOPS/W
            "22nm RRAM":    {"peak_compute": 150.0, "efficiency": 25.0},    # TOPS, TOPS/W
            "3nm GAA":      {"peak_compute": 800.0, "efficiency": 100.0}    # TOPS, TOPS/W
        }
        
        self.packaging = {
            "Monolithic SoC":       {"d2d_bandwidth": 0.0, "added_latency": 0.0},     # GB/s, ns
            "2.5D Chiplet (CoWoS)": {"d2d_bandwidth": 1200.0, "added_latency": 5.0}   # GB/s, ns
        }
        
        self.memory_systems = {
            "On-Chip SRAM":     {"bandwidth": 5000.0},  # GB/s
            "Off-Chip LPDDR5":  {"bandwidth": 100.0},   # GB/s
            "In-Package HBM3e": {"bandwidth": 4800.0}   # GB/s
        }

    def calculate_metrics(self, node_sel, pkg_sel, mem_sel, matrix_dim):
        # 1. Basic Workload Math (GEMM: M=N=K=matrix_dim)
        # Total Floating Point Operations = 2 * N^3
        total_ops = 2 * (matrix_dim ** 3)
        
        # Assume 16-bit precision (2 Bytes per element) for inputs/outputs
        # Matrix A (N*N) + Matrix B (N*N) + Matrix C (N*N)
        total_data_bytes = 3 * (matrix_dim ** 2) * 2
        
        # Arithmetic Intensity = FLOPs / Byte
        arithmetic_intensity = total_ops / total_data_bytes
        
        # 2. Extract Hardware Limits
        peak_compute_tops = self.nodes[node_sel]["peak_compute"]
        peak_compute_flops = peak_compute_tops * 1e12
        
        mem_bw_gbs = self.memory_systems[mem_sel]["bandwidth"]
        mem_bw_bytes = mem_bw_gbs * 1e9
        
        d2d_bw_gbs = self.packaging[pkg_sel]["d2d_bandwidth"]
        
        # 3. Determine Effective Memory/Interconnect Bandwidth
        # If Chiplet architecture is selected, D2D bandwidth alters the effective data rate
        if pkg_sel == "2.5D Chiplet (CoWoS)":
            effective_bw_bytes = min(mem_bw_bytes, d2d_bw_gbs * 1e9)
        else:
            effective_bw_bytes = mem_bw_bytes

        # 4. Roofline Model Calculation
        # Attainable Performance = min(Peak Compute, Arithmetic Intensity * Memory Bandwidth)
        attainable_flops = min(peak_compute_flops, arithmetic_intensity * effective_bw_bytes)
        effective_tops = attainable_flops / 1e12
        
        # 5. Energy Efficiency Scaling (factoring in memory overhead)
        base_efficiency = self.nodes[node_sel]["efficiency"]
        if mem_sel == "Off-Chip LPDDR5":
            system_efficiency = base_efficiency * 0.15  # 85% penalty for off-chip power
        elif mem_sel == "In-Package HBM3e" and pkg_sel == "2.5D Chiplet (CoWoS)":
            system_efficiency = base_efficiency * 0.85  # Minor penalty for interposer PHY
        else:
            system_efficiency = base_efficiency

        # 6. Rule Engine for System Bottlenecks
        bottleneck = "Optimal Balance"
        if pkg_sel == "Monolithic SoC" and matrix_dim > 4096 and mem_sel != "On-Chip SRAM":
            bottleneck = "Reticle Limit Warning: Memory capacity exceeded for a single monolithic die."
        elif mem_sel == "Off-Chip LPDDR5":
            bottleneck = "Memory Wall Bound: System is heavily constrained by off-chip memory bandwidth. Analog CIM macros are starving for data."
        elif pkg_sel == "2.5D Chiplet (CoWoS)" and node_sel == "3nm GAA" and mem_sel == "In-Package HBM3e":
            bottleneck = "Interconnect Overload: Compute arrays are saturated. Performance limited by Die-to-Die PHY cross-talk and latency boundaries."
        elif node_sel == "22nm RRAM" and pkg_sel == "2.5D Chiplet (CoWoS)" and mem_sel == "In-Package HBM3e":
            bottleneck = "Balanced Datacenter Mode: Optimal alignment between high-density analog RRAM compute, D2D interposer channels, and HBM3e throughput."

        return {
            "total_ops": total_ops,
            "arithmetic_intensity": arithmetic_intensity,
            "effective_tops": effective_tops,
            "system_efficiency": system_efficiency,
            "bottleneck": bottleneck,
            "peak_compute_flops": peak_compute_flops,
            "effective_bw_bytes": effective_bw_bytes
        }

    def generate_roofline_plot(self, node_sel, pkg_sel, mem_sel, matrix_dim, metrics, output_path="roofline_plot.png"):
        peak_flops = metrics["peak_compute_flops"]
        bw = metrics["effective_bw_bytes"]
        actual_intensity = metrics["arithmetic_intensity"]
        actual_flops = metrics["effective_tops"] * 1e12
        
        # Calculate inflection point (corner of the roofline)
        inflection_intensity = peak_flops / bw
        
        # Generate x-axis data points (Arithmetic Intensity)
        x_min = min(0.1, actual_intensity * 0.1)
        x_max = max(inflection_intensity * 10, actual_intensity * 10)
        intensities = [x_min, inflection_intensity, x_max]
        
        # Calculate matching y-axis points (Performance in FLOPS)
        perf_limits = [i * bw if i < inflection_intensity else peak_flops for i in intensities]
        
        # Convert performance limits to TOPS for clean plotting
        perf_limits_tops = [p / 1e12 for p in perf_limits]
        
        plt.figure(figsize=(10, 6))
        plt.plot(intensities, perf_limits_tops, label="Roofline Boundary", color="black", linewidth=2)
        plt.scatter([actual_intensity], [metrics["effective_tops"]], color="red", s=100, zorder=5, label="Operating Point")
        
        # Labels and Scale configuration
        plt.xscale("log")
        plt.yscale("log")
        plt.xlabel("Arithmetic Intensity (FLOPs/Byte)", fontsize=12)
        plt.ylabel("Attainable Performance (TOPS)", fontsize=12)
        plt.title(f"Roofline Analysis: {node_sel} | {pkg_sel} | {mem_sel}\nMatrix Dim: {matrix_dim}x{matrix_dim}", fontsize=14)
        plt.grid(True, which="both", linestyle="--", alpha=0.5)
        plt.legend(loc="upper left")
        
        # Annotate operational bottleneck
        plt.annotate(
            f"Current Throughput: {metrics['effective_tops']:.2f} TOPS\nBottleneck: {metrics['bottleneck']}",
            xy=(actual_intensity, metrics["effective_tops"]),
            xytext=(actual_intensity * 1.5, metrics["effective_tops"] * 0.5),
            bbox=dict(boxstyle="round,pad=0.5", fc="yellow", alpha=0.3),
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2")
        )
        
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        print(f"[Success] Roofline plot exported dynamically to: {output_path}")

# --- Execution Entry Point ---
if __name__ == "__main__":
    sim = ProjectMoonshotSimulator()
    
    # Configure parameters to test system scaling
    selected_node = "22nm RRAM"
    selected_pkg = "2.5D Chiplet (CoWoS)"
    selected_mem = "In-Package HBM3e"
    selected_dim = 8192
    
    results = sim.calculate_metrics(selected_node, selected_pkg, selected_mem, selected_dim)
    
    print("="*60)
    print("        PROJECT MOONSHOT ARCHITECTURAL SIMULATOR RESULTS       ")
    print("="*60)
    print(f"Target Configuration: {selected_node} | {selected_pkg} | {selected_mem}")
    print(f"Workload Footprint:   {selected_dim}x{selected_dim} GEMM Execution")
    print(f"Arithmetic Intensity: {results['arithmetic_intensity']:.2f} FLOPs/Byte")
    print("-"*60)
    print(f"Effective Throughput: {results['effective_tops']:.2f} TOPS")
    print(f"System Efficiency:    {results['system_efficiency']:.2f} TOPS/W")
    print(f"Primary Bottleneck:   {results['bottleneck']}")
    print("="*60)
    
    # Save the output visualization trace locally
    sim.generate_roofline_plot(selected_node, selected_pkg, selected_mem, selected_dim, results)
