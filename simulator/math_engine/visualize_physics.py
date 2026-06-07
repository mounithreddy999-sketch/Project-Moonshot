import numpy as np
import matplotlib.pyplot as plt
import os

# Import the math engine we just built
from analog_spatial_model import AnalogSpatialMathEngine

def generate_visualizations():
    # Initialize engine
    engine = AnalogSpatialMathEngine(rows=256, cols=256)
    
    # Extract physical matrices
    v_read_matrix = engine.v_read_matrix
    c_unit_matrix = engine.c_unit_matrix
    
    # Calculate the compiler's pre-distortion matrix
    ideal_cv = engine.base_c_unit * engine.base_v_read
    physical_cv = c_unit_matrix * v_read_matrix
    pre_distortion_matrix = ideal_cv / physical_cv
    
    # Set up the plot
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    # Plot 1: Topographical IR Drop (Voltage Sag)
    # Using 'coolwarm' where lower voltage is blue (cold) and higher is red (hot)
    im0 = axes[0].imshow(v_read_matrix, cmap='coolwarm', origin='lower')
    axes[0].set_title('1. Topographical IR Drop ($V_{read}$ Sag)', fontsize=12)
    axes[0].set_xlabel('Bitlines (Columns)')
    axes[0].set_ylabel('Wordlines (Rows)')
    fig.colorbar(im0, ax=axes[0], label='Voltage (V)')
    
    # Plot 2: Device Mismatch (Capacitance Flaw)
    # Using 'viridis' to show the noisy, random scatter of capacitor sizes
    im1 = axes[1].imshow(c_unit_matrix * 1e15, cmap='viridis', origin='lower')
    axes[1].set_title('2. Device Mismatch (Lithography Variation)', fontsize=12)
    axes[1].set_xlabel('Bitlines (Columns)')
    fig.colorbar(im1, ax=axes[1], label='Capacitance (fF)')
    
    # Plot 3: Compiler Pre-Distortion Matrix
    # Using 'inferno' to show how the compiler mathematically scales the weights 
    # hotter (higher multiplier) in the center to compensate for the voltage drop.
    im2 = axes[2].imshow(pre_distortion_matrix, cmap='inferno', origin='lower')
    axes[2].set_title('3. Software Fix: Compiler Pre-Distortion', fontsize=12)
    axes[2].set_xlabel('Bitlines (Columns)')
    fig.colorbar(im2, ax=axes[2], label='Weight Scale Factor Multiplier')
    
    plt.tight_layout()
    
    # Save the figure to artifacts directory
    artifact_path = r"C:\Users\mouni\.gemini\antigravity-ide\brain\f4b44fa9-a676-4826-83c9-7f5430a405e2\spatial_physics_heatmap.png"
    plt.savefig(artifact_path, dpi=300, bbox_inches='tight')
    print(f"Heatmap successfully saved to: {artifact_path}")

if __name__ == "__main__":
    generate_visualizations()
