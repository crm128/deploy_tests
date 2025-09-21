import streamlit as st
import numpy as np
from scipy.integrate import solve_ivp
import plotly.graph_objects as go
import io
import pandas as pd
from modelo import *

st.set_page_config(
    page_title="TAC",
    page_icon="👋",
)


df = pd.DataFrame()


st.title("Simulador de Arranque - Reactor TAC")

st.sidebar.header("Parámetros de simulación")
Fa0 = st.sidebar.number_input("Flujo A (lb-mol/h)", 1.0, 200.0, 80.0)
Fb0 = st.sidebar.number_input("Flujo B (lb-mol/h)", 1.0, 2000.0, 1000.0)
Fm0 = st.sidebar.number_input("Flujo Inerte (lb-mol/h)", 0.0, 500.0, 100.0)
T0 = st.sidebar.slider("Temperatura inicial (°F)", 30, 130, 75)
Ta1 = st.sidebar.slider("Temperatura del refrigerante (°F)", 20, 200, 60)
UA = st.sidebar.number_input("UA (BTU/h·°F)", 1000.0, 50000.0, 16000.0)
mc = st.sidebar.number_input("Flujo másico refrigerante (lb-mol/h)", 100.0, 5000.0, 1000.0)
V = (1/7.484)*500   

y0 = [0.0, 3.45, 0.0, 0.0, T0]
t_span = (0, 4)
t_eval = np.linspace(0, 4, 300)

sol = solve_ivp(cstr_odes, t_span, y0,
                args=(Fa0, Fb0, Fm0, V, UA, Ta1, mc, T0),
                t_eval=t_eval, method="BDF")

t = sol.t
Ca, Cb, Cc, Cm, T = sol.y

v0 = Fa0/0.923 + Fb0/3.45 + Fm0/1.54
X_final = (Fa0 - Ca[-1] * v0) / Fa0

epsilon = 0.001 
t_est = None

for i in range(1, len(t)):
    crit_Ca = abs(Ca[i] - Ca[i-1]) / max(abs(Ca[i]), 1e-8)
    crit_T = abs(T[i] - T[i-1]) / max(abs(T[i]), 1e-8)
    
    if crit_Ca < epsilon and crit_T < epsilon:
        t_est = t[i]
        break

if t_est is None:
    t_est = "No alcanzado en el rango simulado"




tab1, tab2 = st.tabs(["Funcionamiento","Barrido de parametros"])

with tab1:
    st.markdown(
    """
    ## Guía de uso del Análisis de sensibilidad
    El análisis de sensibilidad permite explorar cómo varían las **variables de salida del reactor** (concentraciones, temperatura, conversión) al modificar de forma sistemática un **parámetro de operación** dentro de un rango definido.
    
    ---

    ### 1. Análisis de sensibilidad (Barrido de parámetros)
    En la pestaña **"Barrido de parámetros"** se estudia cómo cambia el comportamiento del reactor al variar un parámetro dentro de un rango definido.  
    - Se selecciona el parámetro de interés (ej. flujo de A, UA, temperatura del refrigerante, etc.).  
    - Se define el rango inicial y final, así como la cantidad de puntos intermedios.  
    - El simulador ejecuta automáticamente múltiples corridas y muestra:  
    - Tabla con resultados finales.  
    - Gráficos que relacionan el parámetro barrido con las variables de salida (concentraciones, temperatura, conversión).  
    - Posibilidad de graficar dos variables a la vez.  
    - Los resultados se pueden exportar en **CSV o Excel** para análisis externo.

    ---

    ### 2. Objetivo del análisis de sensibilidad
    El análisis de sensibilidad busca:
    - Identificar qué parámetros de operación afectan más el desempeño del reactor.  
    - Explorar condiciones que conduzcan a una operación estable y segura.  
    - Detectar riesgos de runaway térmico o condiciones poco favorables de conversión.  
    - Guiar decisiones de **diseño**, **escalado industrial** o **optimización de operación**.  

    ---

    ### 3. Objetivos del análisis de sensibilidad
    - Identificar **qué parámetros afectan más** la operación del reactor.
    - Evaluar el impacto de variaciones en las condiciones de alimentación o enfriamiento.
    - Estudiar escenarios que conduzcan a **mayor conversión** o **estabilidad térmica**.
    - Anticipar condiciones que podrían llevar a comportamientos inseguros (ej. runaway).


"""
)
    

with tab2:
    st.subheader("Análisis de sensibilidad por barrido de un parámetro")

    # Controles
    param_to_vary = st.selectbox(
        "Parámetro a variar",
        ["Fa0", "Fb0", "Fm0", "T0", "Ta1", "UA", "mc"]
    )
    start_val = st.number_input("Valor inicial", value=50.0)
    end_val = st.number_input("Valor final", value=150.0)
    n_points = st.slider("Cantidad de puntos", 2, 20, 5)

    variables_disp = ["Ca_final", "Cb_final", "Cc_final", "Cm_final", "T_final", "X_final"]
    vars_to_plot = st.multiselect(
        "Selecciona variables a graficar",
        variables_disp,
        default=["X_final", "T_final"]
    )

    if st.button("Ejecutar barrido"):
        results = []

        values = np.linspace(start_val, end_val, n_points)
        for val in values:
            # Copia de parámetros
            Fa, Fb, Fm, T0, UA_, Ta, mc_ = Fa0, Fb0, Fm0, T0, UA, Ta1, mc
            if param_to_vary == "Fa0": Fa = val
            elif param_to_vary == "Fb0": Fb = val
            elif param_to_vary == "Fm0": Fm = val
            elif param_to_vary == "T0": T0 = val
            elif param_to_vary == "UA": UA_ = val
            elif param_to_vary == "Ta1": Ta = val
            elif param_to_vary == "mc": mc_ = val

            # Simulación
            sol = solve_ivp(cstr_odes, t_span, y0,
                            args=(Fa, Fb, Fm, V, UA_, Ta, mc_, T0),
                            t_eval=t_eval, method="BDF")

            Ca, Cb, Cc, Cm, T = sol.y
            v0 = Fa/0.923 + Fb/3.45 + Fm/1.54
            X_final = (Fa - Ca[-1] * v0) / Fa

            results.append({
                param_to_vary: val,
                "Ca_final": Ca[-1],
                "Cb_final": Cb[-1],
                "Cc_final": Cc[-1],
                "Cm_final": Cm[-1],
                "T_final": T[-1],
                "X_final": X_final
            })

        df = pd.DataFrame(results)
        st.dataframe(df)

        fig1 = go.Figure()

        if len(vars_to_plot) > 0:
            fig1.add_trace(go.Scatter(
                x=df[param_to_vary],
                y=df[vars_to_plot[0]],
                mode="lines+markers",
                name=vars_to_plot[0],
                yaxis="y1"
            ))

        if len(vars_to_plot) > 1:
            fig1.add_trace(go.Scatter(
                x=df[param_to_vary],
                y=df[vars_to_plot[1]],
                mode="lines+markers",
                name=vars_to_plot[1],
                yaxis="y2"
            ))

        if len(vars_to_plot) > 2:
            for var in vars_to_plot[2:]:
                fig1.add_trace(go.Scatter(
                    x=df[param_to_vary],
                    y=df[var],
                    mode="lines+markers",
                    name=var,
                    yaxis="y1"
                ))

        # Configuración de los ejes
        fig1.update_layout(
            title=f"Barrido de {param_to_vary}",
            xaxis_title=param_to_vary,
            yaxis=dict(
                title=vars_to_plot[0] if len(vars_to_plot) > 0 else "Valor",
                side="left"
            ),
            yaxis2=dict(
                title=vars_to_plot[1] if len(vars_to_plot) > 1 else "",
                overlaying="y",
                side="right"
            ),
            legend_title="Variables"
        )

        st.plotly_chart(fig1, use_container_width=True)

        

        # Exportación
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Descargar resultados en CSV",
            data=csv,
            file_name=f"barrido_{param_to_vary}.csv",
            mime="text/csv",
            key="barrido_csv"
        )

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Barrido")

        st.download_button(
            label="📊 Descargar resultados en Excel",
            data=output.getvalue(),
            file_name=f"barrido_{param_to_vary}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="barrido_excel"
        )

