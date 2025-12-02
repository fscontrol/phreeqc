from pathlib import Path
import pandas as pd
import plotly.graph_objects as go

from shiny import App, ui, render, reactive, run_app
from shinywidgets import output_widget, render_widget

from lib.run_string import run_phreeqc_simulation

TEMPLATE_PATH = Path(__file__).parent / "config" / "cooling_water.pqi"

app_ui = ui.page_fluid(
    ui.layout_sidebar(
        ui.sidebar(
            ui.h4("Makeup water input"),

            # 🔹 СЮДА ПЕРЕНЁС КНОПКУ — САМЫЙ ВЕРХ САЙДБАРА
            ui.input_action_button(
                "run",
                "▶ Run simulation",      # можно поменять на "▶ Рассчитать"
                class_="btn btn-success btn-lg w-100 mb-3"
            ),

            # cycles сразу под кнопкой, чтоб логически рядом
            ui.input_numeric(
                "cycles",
                "Cycles (concentration factor)",
                7,
                min=1,
                step=0.5,
            ),

            ui.hr(),

            ui.layout_columns(
                ui.input_numeric("pH", "pH", 8.2),
                ui.input_numeric("temp", "Temperature, °C", 30),

                ui.input_numeric("ca_caco3_ppm", "Ca, as CaCO3, ppm", 70),
                ui.input_numeric("mg_caco3_ppm", "Mg, as CaCO3, ppm", 20),

                ui.input_numeric("na_ppm", "Na, ppm", 80),
                ui.input_numeric("cl_ppm", "Cl, ppm", 140),

                ui.input_numeric("so4_ppm", "SO₄, ppm", 90),
                ui.input_numeric("alk_as_caco3_ppm", "Alkalinity as CaCO3, ppm", 120),

                ui.input_numeric("fe_ppm", "Fe, ppm", 0.05),
                ui.input_numeric("sio2_ppm", "SiO₂, ppm", 5),

                ui.input_numeric("po4_ppm", "PO₄, ppm", 1.5),
                ui.input_numeric("co2_log", "log pCO₂(g)", -3.5),

                ui.input_numeric("o2_log", "log pO₂(g)", -0.68),

                col_widths=(6, 6),
            ),

            width="320px",
            open="always",
            class_="bg-light",
        ),

        ui.layout_columns(
            ui.card(
                ui.card_header("Plot"),
                ui.output_ui("y_selector"),
                output_widget("plot"),
            ),
            col_widths={"lg": (9,), "md": (12,)},
        ),
    )
)



def server(input, output, session):
    # сюда кладём последнюю таблицу из PHREEQC
    result_df = reactive.Value(pd.DataFrame())

    @reactive.Effect
    @reactive.event(input.run)
    def _run_simulation():
        cycles = input.cycles()
        if cycles <= 1:
            evaporation_moles = 0.0
        else:
            # 1 кг воды ~ 55.555 моль H2O, убираем долю (1 - 1/cycles)
            evaporation_moles = 55.555 - 55.555 / cycles

        ctx = {
            "pH": input.pH(),
            "temp": input.temp(),

            # из CaCO3 → катион
            # Ca as CaCO3: экв. вес 50, Ca экв. вес 20 → множитель 20/50
            "ca_ppm": input.ca_caco3_ppm() / 50 * 20,
            # Mg as CaCO3: примерно экв. вес ~12 → множитель 12/50
            "mg_ppm": input.mg_caco3_ppm() / 50 * 12,

            "na_ppm": input.na_ppm(),
            "cl_ppm": input.cl_ppm(),

            # SO4 → S: множитель 32/96
            "s_ppm": input.so4_ppm() / 96 * 32,

            # alkalinity as CaCO3 → HCO3⁻: множитель 61/50
            "alk_as_hco3_ppm": input.alk_as_caco3_ppm() / 50 * 61,

            "fe_ppm": input.fe_ppm(),

            # SiO2 → Si
            "si_ppm": input.sio2_ppm() * 28.0855 / 60.089,

            # PO4 → P
            "p_ppm": input.po4_ppm() * 30.97376 / 94.9714,

            "co_2_log": input.co2_log(),
            "o2_log": input.o2_log(),
            "evaporation_moles": evaporation_moles,
        }

        df = run_phreeqc_simulation(TEMPLATE_PATH, ctx)
        result_df.set(df)

    @output
    @render.ui
    def y_selector():
        df = result_df()
        if df.empty:
            return ui.p("Run simulation to select variable")

        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        allowed_cols = [
            col for col in numeric_cols
            if col == "pH" or col.lower().startswith("si_")
        ]

        if not allowed_cols:
            return ui.p("No pH or saturation indices found in SELECTED_OUTPUT")

        default = "pH" if "pH" in allowed_cols else allowed_cols[0]

        return ui.input_select(
            "ycol",
            "Y-axis variable",
            choices=allowed_cols,
            selected=default,
        )

    @output
    @render.table
    def table():
        df = result_df()
        if df.empty:
            return pd.DataFrame()
        return df

    @output
    @render_widget
    def plot():
        df = result_df()
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No data yet",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            fig.update_xaxes(visible=False)
            fig.update_yaxes(visible=False)
            return fig

        # Ось X: cycles, если есть step; иначе — просто индекс
        if "step" in df.columns:
            cycles = input.cycles()
            evaporation_moles = 55.555 - 55.555 / cycles
            df["evap"] = df["step"] * evaporation_moles / df["step"].max()
            df["cycles"] = 55.555 / (55.555 - df["evap"])
            x = df["cycles"]
            xlabel = "Cycles"
        else:
            x = df.index
            xlabel = "Step"

        ycol_input = getattr(input, "ycol", None)
        if ycol_input is None:
            if "pH" in df.columns:
                yname = "pH"
            else:
                yname = df.select_dtypes(include="number").columns[0]
        else:
            yname = ycol_input()

        y = df[yname]

        fig = go.Figure()
        fig.add_scatter(
            x=x,
            y=y,
            mode="lines+markers",
            name=yname,
        )

        fig.update_traces(
            marker=dict(size=7),
            line=dict(width=2),
        )

        fig.update_layout(
            height=700,
            template="seaborn",
            margin=dict(l=60, r=30, t=60, b=60),
            xaxis=dict(
                title=xlabel,
                title_font=dict(size=16),
                tickfont=dict(size=12),
                zeroline=False,
                showgrid=True,
            ),
            yaxis=dict(
                title=yname,
                title_font=dict(size=16),
                tickfont=dict(size=12),
                zeroline=False,
                showgrid=True,
            ),
            font=dict(size=13),
            hovermode="x unified",
        )

        return fig


app = App(app_ui, server)

if __name__ == "__main__":
    run_app(app, host="0.0.0.0", port=8000)
