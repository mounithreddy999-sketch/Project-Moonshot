import numpy as np

class AnalogCIMMathEngine:
    def __init__(self, rows=256, cols=256, adc_resolution=8):
        self.rows = rows
        self.cols = cols
        self.adc_resolution = adc_resolution
        
        # Physical Analog Variables (e.g., Sky130 typicals)
        self.v_read = 0.8  # Read voltage
        self.c_unit = 2.0e-15  # Unit capacitance (2 fF)
        self.c_parasitic = 10.0e-15  # Parasitic bitline capacitance (10 fF)
        
        # Charge injection mismatch parameters
        self.q_inj_mean = 1.5e-16 # Mean charge injection (Coulombs)
        self.q_inj_std = 0.2e-16  # Variation
        
    def _ideal_mac(self, activations, weights):
        """Calculates the perfect, mathematical FP32 dot product."""
        return np.dot(activations, weights)
        
    def _simulate_charge_sharing(self, activations, weights):
        """Simulates the physical charge accumulation on the bitline."""
        
        # Ideal dot product
        ideal_dp = np.dot(activations, weights)
        
        # Calculate ideal bitline voltage (Vbl) based on charge sharing:
        # Vbl = (Sum(W * Act) * C_unit * V_read) / (Rows * C_unit + C_parasitic)
        c_total = (self.rows * self.c_unit) + self.c_parasitic
        v_bl_ideal = (ideal_dp * self.c_unit * self.v_read) / c_total
        
        # Inject physical non-idealities (Charge Injection Drift)
        # Noise matrix: Each cell contributes slightly different parasitic charge
        noise_q = np.random.normal(self.q_inj_mean, self.q_inj_std, ideal_dp.shape)
        
        # In a real array, charge injection scales with the number of active rows,
        # but for this math model, we treat it as a systemic baseline offset.
        v_noise = noise_q / c_total
        
        v_bl_physical = v_bl_ideal + v_noise
        return v_bl_physical
        
    def _adc_quantization(self, v_bl_physical):
        """Quantizes the physical voltage through a simulated ADC."""
        v_max = self.v_read
        levels = 2 ** self.adc_resolution - 1
        
        # Normalize and quantize
        v_norm = np.clip(v_bl_physical / v_max, 0, 1)
        quantized_digital = np.round(v_norm * levels)
        return quantized_digital
        
    def linear_calibration(self, adc_digital, alpha=1.0, beta=0.0):
        """Applies software-level calibration to recover the original math."""
        # V_calibrated = A * V_adc + B
        return (alpha * adc_digital) + beta

    def run_investigation(self):
        print("============================================================")
        print("      PROJECT MOONSHOT: ANALOG MATH INVESTIGATION ENGINE    ")
        print("============================================================")
        
        # Generate random inputs (e.g., 8-bit activations and weights)
        # For simplicity in this math model, let's assume 1 batch, [1 x 256] * [256 x 256]
        act = np.random.randint(0, 2, (1, self.rows)).astype(np.float32)
        weights = np.random.randint(0, 2, (self.rows, self.cols)).astype(np.float32)
        
        print(f"1. Calculating Ideal FP32 Matmul...")
        ideal_dp = self._ideal_mac(act, weights)
        
        print(f"2. Simulating Physical Charge-Sharing & Switch Noise...")
        v_bl_physical = self._simulate_charge_sharing(act, weights)
        
        print(f"3. Executing {self.adc_resolution}-bit ADC Quantization...")
        adc_output = self._adc_quantization(v_bl_physical)
        
        # Derive optimal Alpha and Beta for calibration (Least Squares Fit)
        # In reality, the compiler would derive this during the profiling pass
        print(f"4. Deriving Compiler Calibration Parameters (Alpha, Beta)...")
        # Flatten arrays for fitting
        y = ideal_dp.flatten()
        x = adc_output.flatten()
        A = np.vstack([x, np.ones(len(x))]).T
        alpha, beta = np.linalg.lstsq(A, y, rcond=None)[0]
        
        print(f"   -> Derived Alpha (Scaling): {alpha:.4f}")
        print(f"   -> Derived Beta  (Offset):  {beta:.4f}")
        
        print(f"5. Applying Linear Calibration Recovery...")
        recovered_dp = self.linear_calibration(adc_output, alpha, beta)
        
        mse_raw = np.mean((ideal_dp - adc_output)**2)
        mse_calibrated = np.mean((ideal_dp - recovered_dp)**2)
        
        print("------------------------------------------------------------")
        print(f"Raw ADC Mean Squared Error (Uncalibrated): {mse_raw:.4f}")
        print(f"Recovered Mean Squared Error (Calibrated): {mse_calibrated:.4f}")
        print(f"Signal Recovery Improvement:               {(mse_raw / mse_calibrated):.2f}X")
        print("============================================================")

if __name__ == "__main__":
    engine = AnalogCIMMathEngine(rows=256, cols=256, adc_resolution=8)
    engine.run_investigation()
