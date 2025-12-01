import phreeqpy.iphreeqc.phreeqc_dll as pm
import pandas as pd
from jinja2 import Template
from pathlib import Path
import json

config = json.load(open(Path(__file__).parent.parent / "config/config.json"))
settings = config["phreeqc"]

def run_phreeqc_simulation(template_path: Path, context: dict) -> pd.DataFrame:
    template = Template(template_path.read_text())
    input_string = template.render(**context)
    phreeqc = pm.IPhreeqc(dll_path=settings["dll_path"])
    phreeqc.load_database(settings["db_path"])
    err = phreeqc.get_error_string()
    if err.strip():
        raise RuntimeError(f"Ошибка при load_database:\n{err}")

    # запускаем расчёт
    phreeqc.run_string(input_string)
    err2 = phreeqc.get_error_string()
    if err2.strip():
        raise RuntimeError(f"Ошибка при run_string:\n{err2}")

    out = phreeqc.get_selected_output_array()
    print(out)

    # out[0] — заголовки, остальные строки — данные
    df = pd.DataFrame(out[1:], columns=out[0])

    # Приводим числовые колонки к float (по желанию)
    for col in df.columns:
        with pd.option_context("mode.chained_assignment", None):
            df[col] = pd.to_numeric(df[col], errors="ignore")
    return df


