import numpy as np

class UCIeChipletMesh:
    def __init__(self, grid_size=(2, 2)):
        """
        Simulates a 2D mesh of heterogeneous chiplets connected via UCIe 
        (Universal Chiplet Interconnect Express).
        """
        self.grid_size = grid_size
        self.num_chiplets = grid_size[0] * grid_size[1]
        
        # UCIe 1.0 Advanced Package Metrics
        self.bandwidth_per_edge_GBs = 2000.0  # 2 TB/s per beachfront edge
        self.hop_latency_ns = 5.0             # 5ns base latency per die-to-die hop
        self.energy_per_bit_pJ = 0.25         # 0.25 pJ/bit transmission energy
        
    def _get_coordinates(self, chiplet_id):
        row = chiplet_id // self.grid_size[1]
        col = chiplet_id % self.grid_size[1]
        return row, col
        
    def _calculate_manhattan_distance(self, src_id, dst_id):
        if src_id >= self.num_chiplets or dst_id >= self.num_chiplets:
            raise ValueError("Chiplet ID out of bounds.")
        src_r, src_c = self._get_coordinates(src_id)
        dst_r, dst_c = self._get_coordinates(dst_id)
        return abs(src_r - dst_r) + abs(src_c - dst_c)

    def route_tensor(self, tensor_shape, src_id, dst_id, dtype_bits=16):
        """
        Simulates transmitting an intermediate PyTorch tensor across the UCIe mesh.
        """
        num_elements = np.prod(tensor_shape)
        total_bits = num_elements * dtype_bits
        total_bytes = total_bits / 8
        
        distance = self._calculate_manhattan_distance(src_id, dst_id)
        
        if distance == 0:
            return {"latency_ns": 0.0, "energy_pJ": 0.0, "hops": 0}
            
        # 1. Bandwidth Delay: Time taken to serialize the bytes across the beachfront
        # (Bytes / (Bytes/sec)) * 1e9 ns/sec
        serialization_delay_ns = (total_bytes / (self.bandwidth_per_edge_GBs * 1e9)) * 1e9
        
        # 2. Propagation Delay: Time taken to traverse the physical routing hops
        propagation_delay_ns = distance * self.hop_latency_ns
        
        total_latency_ns = serialization_delay_ns + propagation_delay_ns
        
        # 3. Energy Penalty: Energy to drive the UCIe PHYs across the hops
        total_energy_pJ = total_bits * self.energy_per_bit_pJ * distance
        
        return {
            "tensor_size_MB": total_bytes / (1024**2),
            "hops": distance,
            "serialization_delay_ns": serialization_delay_ns,
            "propagation_delay_ns": propagation_delay_ns,
            "total_latency_ns": total_latency_ns,
            "total_energy_nJ": total_energy_pJ / 1000.0
        }

    def simulate_llm_routing_pipeline(self):
        print("============================================================")
        print("      PROJECT MOONSHOT: UCIE CHIPLET INTERCONNECT MESH      ")
        print("============================================================")
        
        print(f"[*] Initialized {self.grid_size[0]}x{self.grid_size[1]} Chiplet Mesh.")
        print(f"[*] UCIe Metrics: {self.bandwidth_per_edge_GBs} GB/s bandwidth, {self.hop_latency_ns}ns/hop, {self.energy_per_bit_pJ} pJ/bit")
        
        # Simulating a massive LLM activation tensor (e.g. Batch=1, Seq=4096, Dim=4096, FP16)
        tensor_shape = (1, 4096, 4096)
        
        # Route 1: Neighboring Chiplets (0 -> 1)
        print("\n[ROUTE 1] Neighboring Hop (Chiplet 0 -> Chiplet 1)")
        res1 = self.route_tensor(tensor_shape, 0, 1)
        print(f"  -> Transferred {res1['tensor_size_MB']:.2f} MB across {res1['hops']} hop(s).")
        print(f"  -> Serialization Latency: {res1['serialization_delay_ns']:.2f} ns")
        print(f"  -> Propagation Latency: {res1['propagation_delay_ns']:.2f} ns")
        print(f"  -> Total Network Latency Penalty: {res1['total_latency_ns']:.2f} ns")
        print(f"  -> Total Energy Penalty: {res1['total_energy_nJ']:.2f} nJ")
        
        # Route 2: Diagonal Cross-Mesh Routing (0 -> 3)
        print("\n[ROUTE 2] Diagonal Mesh Hop (Chiplet 0 -> Chiplet 3)")
        res2 = self.route_tensor(tensor_shape, 0, 3)
        print(f"  -> Transferred {res2['tensor_size_MB']:.2f} MB across {res2['hops']} hop(s).")
        print(f"  -> Serialization Latency: {res2['serialization_delay_ns']:.2f} ns")
        print(f"  -> Propagation Latency: {res2['propagation_delay_ns']:.2f} ns")
        print(f"  -> Total Network Latency Penalty: {res2['total_latency_ns']:.2f} ns")
        print(f"  -> Total Energy Penalty: {res2['total_energy_nJ']:.2f} nJ")
        print("============================================================")

if __name__ == "__main__":
    mesh = UCIeChipletMesh(grid_size=(2, 2))
    mesh.simulate_llm_routing_pipeline()
