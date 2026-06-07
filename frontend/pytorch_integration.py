import torch
import torch.nn as nn
import math
import sys
import os

# Append parent dir to path to import the optimizer pass
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from compiler.passes.tile_optimizer import MLIRTileOptimizer

class AnalogCIMLinear(nn.Module):
    """
    A custom PyTorch module that intercepts standard linear layers and 
    prepares them for MLIR lowering to the Project Moonshot analog CIM macro.
    """
    def __init__(self, in_features, out_features, bias=True):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        
        # Initialize the hardware-aware optimizer (Targeting 2MB SRAM, 125 FLOPs/Byte roofline)
        self.optimizer = MLIRTileOptimizer(sram_capacity_kb=2048, roofline_inflection_flops_per_byte=125)
        
        # Standard weights
        self.weight = nn.Parameter(torch.Tensor(out_features, in_features))
        if bias:
            self.bias = nn.Parameter(torch.Tensor(out_features))
        else:
            self.register_parameter('bias', None)
            
        self.reset_parameters()

    def reset_parameters(self):
        nn.init.kaiming_uniform_(self.weight, a=math.sqrt(5))
        if self.bias is not None:
            fan_in, _ = nn.init._calculate_fan_in_and_fan_out(self.weight)
            bound = 1 / math.sqrt(fan_in)
            nn.init.uniform_(self.bias, -bound, bound)

    def forward(self, input):
        # In standard execution (e.g. CPU fallback), perform standard matmul
        if not torch.jit.is_tracing() and not self.use_analog_compiler_path():
            return nn.functional.linear(input, self.weight, self.bias)
        
        # In compiler tracing mode, emit custom MLIR Transform payloads
        return self._emit_moonshot_transform(input)
        
    def use_analog_compiler_path(self):
        return True
        
    def _emit_moonshot_transform(self, input):
        """
        Calculates the optimal tile size for the current matrix dimensions and
        emits the declarative MLIR Transform Dialect payload. Crucially, it instructs 
        the compiler to pad residual edge tiles LOCALLY on the chiplet's SRAM, 
        saving precious D2D bandwidth.
        """
        # Batch dimension is 'M', input feature is 'K', output feature is 'N'
        # PyTorch linear is: Input(M, K) x Weight(N, K)^T -> Output(M, N)
        M = input.shape[0] if len(input.shape) > 1 else 1
        K = self.in_features
        N = self.out_features
        
        print(f"[PyTorch Frontend] Intercepting linalg.matmul -> M={M}, K={K}, N={N}")
        
        # 1. Query the Optimizer for the Physics-Bound Tile Size
        optimal_tile = self.optimizer.find_optimal_square_tile()
        if not optimal_tile:
            raise RuntimeError("Failed to find a valid tile size satisfying hardware boundaries.")
            
        T = optimal_tile['Tm'] # The magic 576
        
        # 2. Check for Residual Edge Tiles (For Analytics)
        has_residuals = (M % T != 0) or (K % T != 0) or (N % T != 0)
        
        # 3. Emit the MLIR Transform Payload
        mlir_payload = f"""
// --- Project Moonshot: MLIR Transform Payload ---
// Matrix Shape: [{M}, {N}, {K}]
// Hardware Target: 2.5D CoWoS | 22nm RRAM CIM
transform.sequence failures(propagate) {{
^bb0(%arg1: !transform.any_op):
  // 1. Locate the tensor computation in the payload IR
  %matmul = transform.structured.match ops{{["linalg.matmul"]}} in %arg1
  
  // 2. Tile to the mathematically proven roofline boundary (T={T})
  %tiled_loops, %tiled_matmul = transform.structured.tile_using_for %matmul 
                                tile_sizes [{T}, {T}, {T}]
"""
        # 4. Inject Localized Padding if Residuals Exist
        if has_residuals:
            mlir_payload += f"""
  // 3. Residual handling: Pad edge tiles locally inside the CIM Macro's 2MB SRAM.
  //    Avoids zero-transmissions over the D2D interconnect. Requires WL/BL hardware gating.
  %padded = transform.structured.pad %tiled_matmul
            padding_values [0.0 : f16, 0.0 : f16, 0.0 : f16]
            padding_dimensions [0, 1, 2]
"""
        mlir_payload += "}\n"
        
        print("\n[PyTorch Frontend] Emitted Transform Dialect:")
        print(mlir_payload)
        
        # Mock actual execution for graph traversal continuation
        return nn.functional.linear(input, self.weight, self.bias)

if __name__ == "__main__":
    print("Project Moonshot - PyTorch to MLIR Transform Bridge")
    print("=" * 60)
    
    # Simulate a massive LLM layer (e.g. 8192 tokens)
    dummy_input = torch.randn(8192, 8192) 
    analog_layer = AnalogCIMLinear(in_features=8192, out_features=8192)
    
    output = analog_layer(dummy_input)
