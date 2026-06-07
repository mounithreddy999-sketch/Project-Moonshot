import numpy as np

class AnalogSpatialMathEngine:
    def __init__(self, rows=256, cols=256, adc_resolution=8):
        self.rows = rows
        self.cols = cols
        self.adc_resolution = adc_resolution
        
        # Base physical variables
        self.base_v_read = 0.8  
        self.base_c_unit = 2.0e-15  
        self.c_parasitic = 10.0e-15  
        
        # 1. SPATIAL DEVICE MISMATCH: Gaussian distribution of unit capacitance across the array
        # e.g., 5% standard deviation in capacitance due to lithography limits
        self.c_unit_matrix = np.random.normal(self.base_c_unit, self.base_c_unit * 0.05, (rows, cols))
        
        # 2. TOPOGRAPHICAL IR DROP: Voltage sags towards the center of the array
        self.v_read_matrix = self._generate_ir_drop_map(severity=0.20) # 20% max drop at center
        
    def _generate_ir_drop_map(self, severity=0.20):
        """Generates a 2D spatial voltage map where center pixels sag."""
        v_map = np.zeros((self.rows, self.cols))
        center_r, center_c = self.rows // 2, self.cols // 2
        max_dist = np.sqrt(center_r**2 + center_c**2)
        
        for r in range(self.rows):
            for c in range(self.cols):
                dist = np.sqrt((r - center_r)**2 + (c - center_c)**2)
                # Max sag at distance 0 (center), minimum sag at max_dist (edges)
                sag = severity * (1.0 - (dist / max_dist))
                v_map[r, c] = self.base_v_read * (1.0 - sag)
        return v_map

    def _ideal_mac(self, activations, weights):
        return np.dot(activations, weights)
        
    def _simulate_charge_sharing(self, activations, weights, v_read_matrix):
        """Simulates dot product with spatial physical matrices."""
        
        # Broadcast activations to match weight matrix: (256, 1) -> (256, 256)
        act_broadcast = np.broadcast_to(activations.T, weights.shape)
        
        # Calculate charge per cell: Q_cell = Act * W * C_unit_xy * V_read_xy
        q_matrix = act_broadcast * weights * self.c_unit_matrix * v_read_matrix
        
        # Accumulate charge down the columns (bitlines)
        total_q_bl = np.sum(q_matrix, axis=0)
        
        # Calculate total capacitance per bitline: sum(C_unit_y) + C_parasitic
        c_total_bl = np.sum(self.c_unit_matrix, axis=0) + self.c_parasitic
        
        # Vbl = Q_total / C_total
        v_bl_physical = total_q_bl / c_total_bl
        
        # Add random thermal switch noise (global)
        q_inj_mean, q_inj_std = 1.5e-16, 0.2e-16
        noise_v = np.random.normal(q_inj_mean, q_inj_std, v_bl_physical.shape) / c_total_bl
        
        return v_bl_physical + noise_v
        
    def _adc_quantization(self, v_bl_physical):
        levels = 2 ** self.adc_resolution - 1
        # ADC references global base_v_read
        v_norm = np.clip(v_bl_physical / self.base_v_read, 0, 1)
        return np.round(v_norm * levels)

    def run_spatial_investigation(self):
        print("============================================================")
        print("   PROJECT MOONSHOT: SPATIAL PHYSICS & PRE-DISTORTION       ")
        print("============================================================")
        
        act = np.random.randint(0, 2, (1, self.rows)).astype(np.float32)
        weights = np.random.randint(0, 2, (self.rows, self.cols)).astype(np.float32)
        
        ideal_dp = self._ideal_mac(act, weights)
        
        # --- PHASE 1: UNMITIGATED SPATIAL PHYSICS ---
        print("\n[PHASE 1] Unmitigated Array (Center Sag & 5% Device Mismatch)")
        physical = self._simulate_charge_sharing(act, weights, self.v_read_matrix)
        adc = self._adc_quantization(physical)
        
        mse_raw = np.mean((ideal_dp - adc)**2)
        print(f"  -> Raw Mean Squared Error: {mse_raw:.4f}")
        
        # --- PHASE 2: HARDWARE MITIGATION (Tighten PDN) ---
        print("\n[PHASE 2] Hardware Mitigation (Tighten PDN grid, flatten IR Drop)")
        # We simulate a better PDN by reducing the severity from 20% to 5%
        hw_v_read_matrix = self._generate_ir_drop_map(severity=0.05)
        hw_physical = self._simulate_charge_sharing(act, weights, hw_v_read_matrix)
        hw_adc = self._adc_quantization(hw_physical)
        
        mse_hw = np.mean((ideal_dp - hw_adc)**2)
        print(f"  -> Hardware Mitigated MSE: {mse_hw:.4f}")
        
        # --- PHASE 3: SOFTWARE MITIGATION (Weight Pre-Distortion) ---
        print("\n[PHASE 3] Software Mitigation (Weight Pre-Distortion Compiler Pass)")
        # The compiler knows the exact v_read_matrix and c_unit_matrix.
        # It intentionally over-scales the weights before deployment to counteract the IR drop.
        # Scale Factor = (Base_C_unit * Base_V_read) / (Cell_C_unit * Cell_V_read)
        ideal_cv = self.base_c_unit * self.base_v_read
        physical_cv = self.c_unit_matrix * self.v_read_matrix
        pre_distortion_matrix = ideal_cv / physical_cv
        
        # The compiler pre-distorts the weights 
        distorted_weights = weights * pre_distortion_matrix
        
        # Simulate execution on the highly flawed physical array using pre-distorted weights
        sw_physical = self._simulate_charge_sharing(act, distorted_weights, self.v_read_matrix)
        sw_adc = self._adc_quantization(sw_physical)
        
        mse_sw = np.mean((ideal_dp - sw_adc)**2)
        print(f"  -> Software Mitigated MSE (Pre-Distortion): {mse_sw:.4f}")
        
        print("\n============================================================")

if __name__ == "__main__":
    engine = AnalogSpatialMathEngine(rows=256, cols=256, adc_resolution=8)
    engine.run_spatial_investigation()
