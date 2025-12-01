import phreeqpy.iphreeqc.phreeqc_dll as pm
import pandas as pd
from lib.run_string import run_phreeqc_simulation, config
from pathlib import Path

template_path = Path(__file__).parent / "config/cooling_water.pqi"
context = {
    "pH": 8.2,
    "temp": 30,
    "ca_ppm": 70,
    "mg_ppm": 20,
    "na_ppm": 80,
    "cl_ppm": 140,
    "s_ppm": 90,
    "alk_as_hco3_ppm": 120,
    "fe_ppm": 0.05,
    "si_ppm": 5,
    "p_ppm": 1.5,
    "co_2_log": -3.5,
    "o2_log": 0.0,
    "evaporation_moles": 0.1,
}
df = run_phreeqc_simulation(template_path, context)
print(df)
