import sys
import os
import asyncio
import json
import logging
import numpy as np
import time

# Add math_engine to path so we can import our simulation engines
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'math_engine')))

from analog_thermal_drift import AnalogThermalMathEngine
from aiokafka import AIOKafkaProducer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def stream_thermal_telemetry():
    topic = "moonshot.telemetry.analog_thermal"
    bootstrap_servers = "localhost:9092"
    
    # Initialize Kafka producer using AURA's exact aiokafka logic
    try:
        producer = AIOKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await producer.start()
        logger.info(f"Connected to AURA Kafka broker at {bootstrap_servers}. Streaming to {topic}...")
    except Exception as e:
        logger.error(f"Failed to connect to Kafka. Ensure AURA's Kafka broker is running: {e}")
        return

    # Initialize Moonshot Math Engine
    engine = AnalogThermalMathEngine(rows=256, cols=256, adc_resolution=8)
    
    act = np.random.randint(0, 2, (1, 256)).astype(np.float32)
    weights = np.random.randint(0, 2, (256, 256)).astype(np.float32)
    ideal_dp = engine._ideal_mac(act, weights)
    
    logger.info("Initiating LLM Batch Inference. Simulating Dynamic Thermal Drift...")
    
    try:
        # T=0 Calibration Profiling (Static baseline)
        alpha_opt, beta_opt = engine.profile_array(act, weights)
        
        # Simulate an increasing thermal envelope over time
        for t in range(50): # 50 streaming steps
            thermal_multiplier = 1.0 + (t * 0.05) # Chip heats up 5% per step
            
            # Phase 1: Unmitigated Static Profiling (Failure)
            v_static = engine._simulate_charge_sharing(act, weights, thermal_multiplier)
            adc_static = engine._adc_quantization(v_static)
            hw_static = (adc_static * alpha_opt) + beta_opt
            mse_static = float(np.mean((ideal_dp - hw_static)**2))
            
            # Phase 2: Adaptive Compiler Profiling (Success)
            alpha_adapt, beta_adapt = engine.profile_array(act, weights, thermal_multiplier)
            v_adapt = engine._simulate_charge_sharing(act, weights, thermal_multiplier)
            adc_adapt = engine._adc_quantization(v_adapt)
            hw_adapt = (adc_adapt * alpha_adapt) + beta_adapt
            mse_adapt = float(np.mean((ideal_dp - hw_adapt)**2))
            
            # Construct the AURA-compatible JSON Payload
            record = {
                "timestamp": time.time(),
                "time_step": t,
                "hardware_metrics": {
                    "thermal_drift_multiplier": round(thermal_multiplier, 3),
                    "ir_drop_sag_percent": round((thermal_multiplier - 1.0) * 15, 2),
                },
                "accuracy_metrics": {
                    "unmitigated_mse": round(mse_static, 4),
                    "compiler_mitigated_mse": round(mse_adapt, 4),
                    "compiler_alpha_applied": round(alpha_adapt, 4)
                },
                "status": "CRITICAL_DRIFT" if mse_static > 10.0 else "NOMINAL"
            }
            
            logger.info(f"Stream [t={t}] | Drift: {thermal_multiplier:.2f}X | Unmitigated MSE: {mse_static:.2f} | Status: {record['status']}")
            
            # Send to AURA Kafka
            await producer.send_and_wait(topic, record)
            await asyncio.sleep(0.5) # Stream 2 records per second
            
    except KeyboardInterrupt:
        logger.info("Streaming manually interrupted by user.")
    except Exception as e:
        logger.error(f"Streaming failed: {e}")
    finally:
        await producer.stop()
        logger.info("Kafka Producer shut down gracefully.")

if __name__ == "__main__":
    asyncio.run(stream_thermal_telemetry())
