import numpy as np

class AnalogThermalMathEngine:
    def __init__(self, rows=256, cols=256, adc_resolution=8):
        self.rows = rows
        self.cols = cols
        self.adc_resolution = adc_resolution
        
        # Physical Analog Variables
        self.v_read = 0.8  
        self.c_unit = 2.0e-15  
        self.c_parasitic = 10.0e-15  
        
        # Base Charge injection mismatch parameters
        self.base_q_inj_mean = 1.5e-16 # Mean charge injection at T=0
        self.q_inj_std = 0.2e-16  
        
    def _ideal_mac(self, activations, weights):
        return np.dot(activations, weights)
        
    def _simulate_charge_sharing(self, activations, weights, thermal_drift_multiplier=1.0):
        ideal_dp = np.dot(activations, weights)
        c_total = (self.rows * self.c_unit) + self.c_parasitic
        
        # As temperature increases, metal resistance increases, V_read sags (IR drop)
        current_v_read = self.v_read * (1.0 - 0.15 * (thermal_drift_multiplier - 1.0))
        
        v_bl_ideal = (ideal_dp * self.c_unit * current_v_read) / c_total
        
        # Apply Thermal Drift to the mean injection charge (exponential increase with temp)
        current_q_inj_mean = self.base_q_inj_mean * (thermal_drift_multiplier ** 2)
        
        noise_q = np.random.normal(current_q_inj_mean, self.q_inj_std, ideal_dp.shape)
        v_noise = noise_q / c_total
        v_bl_physical = v_bl_ideal + v_noise
        return v_bl_physical
        
    def _adc_quantization(self, v_bl_physical):
        v_max = self.v_read
        levels = 2 ** self.adc_resolution - 1
        v_norm = np.clip(v_bl_physical / v_max, 0, 1)
        quantized_digital = np.round(v_norm * levels)
        return quantized_digital
        
    def derive_calibration(self, ideal_dp, adc_output):
        y = ideal_dp.flatten()
        x = adc_output.flatten()
        A = np.vstack([x, np.ones(len(x))]).T
        alpha, beta = np.linalg.lstsq(A, y, rcond=None)[0]
        return alpha, beta

    def run_thermal_investigation(self):
        print("============================================================")
        print("   PROJECT MOONSHOT: DYNAMIC THERMAL DRIFT INVESTIGATION    ")
        print("============================================================")
        
        time_steps = 4
        # We will simulate processing 4 sequential batches. 
        # Over time, the chip heats up, increasing the charge injection mean by 50% per step.
        drift_multipliers = [1.0, 1.5, 2.0, 2.5] 
        
        # --- PHASE 1: STATIC CALIBRATION FAILURE ---
        print("\n[PHASE 1] Static Calibration (Calibrating only at T=0)")
        
        # Profiling at T=0
        prof_act = np.random.randint(0, 2, (1, self.rows)).astype(np.float32)
        prof_weights = np.random.randint(0, 2, (self.rows, self.cols)).astype(np.float32)
        prof_ideal = self._ideal_mac(prof_act, prof_weights)
        prof_physical = self._simulate_charge_sharing(prof_act, prof_weights, thermal_drift_multiplier=1.0)
        prof_adc = self._adc_quantization(prof_physical)
        
        static_alpha, static_beta = self.derive_calibration(prof_ideal, prof_adc)
        print(f"  -> T=0 Profile Derived: Alpha={static_alpha:.4f}, Beta={static_beta:.4f}")
        
        for t in range(time_steps):
            act = np.random.randint(0, 2, (1, self.rows)).astype(np.float32)
            weights = np.random.randint(0, 2, (self.rows, self.cols)).astype(np.float32)
            ideal = self._ideal_mac(act, weights)
            
            # Simulate physical hardware at current thermal drift
            physical = self._simulate_charge_sharing(act, weights, drift_multipliers[t])
            adc = self._adc_quantization(physical)
            
            # Apply STATIC calibration
            recovered = (static_alpha * adc) + static_beta
            mse = np.mean((ideal - recovered)**2)
            print(f"  Time t={t} | Thermal Drift: {drift_multipliers[t]:.1f}X | MSE: {mse:.4f}")

        # --- PHASE 2: ADAPTIVE CALIBRATION RECOVERY ---
        print("\n[PHASE 2] Adaptive Compiler Profiling (Re-calibrating every step)")
        
        for t in range(time_steps):
            # 1. Compiler Profiling Pause (Simulating dynamic profiling)
            prof_act = np.random.randint(0, 2, (1, self.rows)).astype(np.float32)
            prof_weights = np.random.randint(0, 2, (self.rows, self.cols)).astype(np.float32)
            prof_ideal = self._ideal_mac(prof_act, prof_weights)
            prof_physical = self._simulate_charge_sharing(prof_act, prof_weights, drift_multipliers[t])
            prof_adc = self._adc_quantization(prof_physical)
            
            dynamic_alpha, dynamic_beta = self.derive_calibration(prof_ideal, prof_adc)
            
            # 2. Neural Network Execution
            act = np.random.randint(0, 2, (1, self.rows)).astype(np.float32)
            weights = np.random.randint(0, 2, (self.rows, self.cols)).astype(np.float32)
            ideal = self._ideal_mac(act, weights)
            physical = self._simulate_charge_sharing(act, weights, drift_multipliers[t])
            adc = self._adc_quantization(physical)
            
            # Apply DYNAMIC calibration
            recovered = (dynamic_alpha * adc) + dynamic_beta
            mse = np.mean((ideal - recovered)**2)
            print(f"  Time t={t} | Thermal Drift: {drift_multipliers[t]:.1f}X | Re-Profiled Alpha={dynamic_alpha:.4f} | MSE: {mse:.4f}")
            
        print("============================================================")

if __name__ == "__main__":
    engine = AnalogThermalMathEngine(rows=256, cols=256, adc_resolution=8)
    engine.run_thermal_investigation()
