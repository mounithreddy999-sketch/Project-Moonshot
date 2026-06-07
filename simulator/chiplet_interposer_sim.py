class ChipletInterposerSim:
    """
    Architectural Simulator for the Project Moonshot 2.5D Interposer.
    
    This models the bandwidth and latency bottlenecks of moving data across 
    an interposer (e.g., TSMC CoWoS) between a 3nm digital orchestrator, 
    HBM3e memory stacks, and 22nm Analog CIM compute chiplets.
    """
    def __init__(self, num_cim_chiplets=4, hbm_bandwidth_gbps=4800):
        self.num_cim_chiplets = num_cim_chiplets
        self.hbm_bandwidth_gbps = hbm_bandwidth_gbps
        
        # Interposer Die-to-Die (D2D) PHY characteristics (e.g. UCIe or custom AIB)
        self.d2d_bandwidth_per_chiplet_gbps = 512 
        self.d2d_latency_ns = 5.0 
        
        # CIM Chiplet characteristics (22nm RRAM)
        self.cim_tops_per_chiplet = 250 # Tera-Operations Per Second (INT8 eq)
        self.cim_efficiency_tops_w = 15.0 # Assuming massive analog efficiency leap
        
    def simulate_matmul(self, M, K, N):
        """
        Simulates the execution of an MxK * KxN matrix multiplication.
        Evaluates the balance between compute bounds and memory bounds.
        """
        # 1. Total Operations (MACs)
        total_ops = 2 * M * K * N 
        
        # 2. Data Movement (Bytes)
        # Assuming INT8 activations and weights
        bytes_activations = M * K
        bytes_weights = K * N
        bytes_output = M * N * 4 # FP32 accumulation out
        
        total_data_bytes = bytes_activations + bytes_weights + bytes_output
        
        # 3. Compute Time (Assuming perfect distribution across chiplets)
        total_compute_tops = self.cim_tops_per_chiplet * self.num_cim_chiplets
        compute_time_ms = (total_ops / 1e12) / total_compute_tops * 1000
        
        # 4. Memory/Interposer Bottleneck Time
        # Data must move from HBM -> Digital Orchestrator -> D2D PHY -> CIM Chiplet
        total_d2d_bandwidth = self.d2d_bandwidth_per_chiplet_gbps * self.num_cim_chiplets
        bottleneck_bw = min(self.hbm_bandwidth_gbps, total_d2d_bandwidth)
        
        memory_time_ms = (total_data_bytes / 1e9) / bottleneck_bw * 1000
        
        # Execution is bounded by the slower of the two (Roofline model approximation)
        total_time_ms = max(compute_time_ms, memory_time_ms) + (self.d2d_latency_ns / 1e6)
        
        utilization = compute_time_ms / total_time_ms
        
        return {
            "total_time_ms": total_time_ms,
            "compute_bound": compute_time_ms > memory_time_ms,
            "utilization": utilization,
            "power_estimated_w": total_compute_tops / self.cim_efficiency_tops_w
        }

if __name__ == "__main__":
    print("Project Moonshot - 2.5D Interposer Architectural Simulator")
    sim = ChipletInterposerSim(num_cim_chiplets=8)
    
    # Simulate a massive LLM projection layer: 4096 tokens, 8192 in, 8192 out
    results = sim.simulate_matmul(4096, 8192, 8192)
    
    print("\nSimulation Results (4096x8192 * 8192x8192):")
    print(f"  Execution Time : {results['total_time_ms']:.4f} ms")
    print(f"  Bound By       : {'Compute' if results['compute_bound'] else 'Memory/Interposer Bandwidth'}")
    print(f"  HW Utilization : {results['utilization']*100:.1f} %")
    print(f"  Est. Power     : {results['power_estimated_w']:.1f} W")
