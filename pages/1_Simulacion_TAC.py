import streamlit as st
import numpy as np
from scipy.integrate import solve_ivp
import plotly.graph_objects as go
import pandas as pd
from modelo import *

st.set_page_config(
    page_title="TAC",
    page_icon="👋",
)


df = pd.DataFrame()


st.set_page_config(page_title="Simulador TAC", layout="wide")
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




tab1, tab2, tab3, tab4 = st.tabs(["Funcionamiento","Resultados Numéricos", "Gráficas", "Configuración"])
with tab1:
    st.markdown(
    """
    # Guía de uso del Simulador TAC

    Este simulador reproduce el **arranque dinámico de un reactor continuo agitado (TAC / CSTR)** aplicado a la **producción de propilenglicol** a partir de la hidrólisis del óxido de propileno.  
    El modelo resuelve de forma numérica los **balances de materia y energía**, permitiendo observar cómo evolucionan las variables del proceso hasta alcanzar el estado estacionario.

    ---

    ## 1. ¿Qué representa el modelo?
    - El reactor se alimenta con:
        - **A**: óxido de propileno.  
        - **B**: agua (reactivo).  
        - **Inerte**: un componente no reactivo para ajustar la dilución.  
    - La reacción global es:  

      $$
      C_{3}H_{6}O + H_{2}O \; \longrightarrow \; C_{3}H_{8}O_{2}
      $$

      donde se forma **propilenglicol**.  
    - Se incluyen efectos de transferencia de calor mediante un intercambiador con coeficiente global $UA$ y flujo másico del refrigerante $m_c$.  

    ---

    ## 2. Uso básico del simulador
    1. En la **barra lateral** se configuran los parámetros de operación:  
       - Flujos molares de A, B e inerte.  
       - Temperatura inicial del reactor ($T_0$).  
       - Temperatura del refrigerante ($T_a$).  
       - Parámetros de transferencia de calor: $UA$ y $m_c$.  

    2. Al ejecutar la simulación, el programa calcula:  
       - Evolución temporal de la concentracion de $C_A.  
       - Evolución de la temperatura ($T$).  
       - Conversión de A ($X_A$).  
       - Estimación del **tiempo de estabilización** del reactor.  

    ---

    ## 3. Resultados obtenidos
    - **Gráficas dinámicas**:
        - Concentración vs. tiempo.  
        - Temperatura vs. tiempo (con límite de seguridad).  
        - Diagrama de fase concentración-temperatura.  
    - **Resumen de parámetros** empleados en la simulación.  

    ---
    """
    )

with tab2:
    st.subheader("Valores finales de la simulación")
    st.write(f"**Ca final:** {Ca[-1]:.3f} lb-mol/pie3")
    st.write(f"**Cb final:** {Cb[-1]:.3f} lb-mol/pie3")
    st.write(f"**Cc final:** {Cc[-1]:.3f} lb-mol/pie3")
    st.write(f"**Cm final:** {Cm[-1]:.3f} lb-mol/pie3")
    st.write(f"**T final:** {T[-1]:.2f} °F")
    st.write(f"**Conversión final de A:** {X_final:.3f}")
    st.write(f"**Tiempo de estabilización:** {t_est:.2f} horas")

with tab3:
    st.subheader("Evolución temporal")

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=t, y=Ca, mode="lines", name="Ca"))
    fig1.update_layout(title="Concentraciones vs Tiempo",
                       xaxis_title="Tiempo (h)", yaxis_title="Concentración (lb-mol/L)")

    if isinstance(t_est, (float, int)):
        fig1.add_vline(x=t_est, line=dict(color="blue", dash="dot"),
                       annotation_text=f"Estabilización {t_est:.2f} h",
                       annotation_position="top right")
    st.plotly_chart(fig1, use_container_width=True)

    T_lim = 180 
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=t, y=T, mode="lines", name="T", line=dict(color="red")))
    fig2.add_hline(y=T_lim, line=dict(color="red", dash="dash"), 
               annotation_text=f"Límite {T_lim} °K", annotation_position="top left")
    fig2.update_layout(title="Temperatura vs Tiempo",
                       xaxis_title="Tiempo (h)", yaxis_title="Temperatura (°F)")

    if isinstance(t_est, (float, int)):
        fig2.add_vline(x=t_est, line=dict(color="blue", dash="dot"),
                       annotation_text=f"Estabilización {t_est:.2f} h",
                       annotation_position="top right")
    st.plotly_chart(fig2, use_container_width=True)

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=T, y=Ca, mode="lines", name="Ca(T)", line=dict(color="green")))
    fig3.add_vline(x=T_lim, line=dict(color="red", dash="dash"), 
               annotation_text=f"Límite {T_lim} °K", annotation_position="top left")
    fig3.update_layout(title="Concentración vs Temperatura",
                       xaxis_title="Temperatura (°K)", yaxis_title="Ca (lb-mol/pie3)")
    st.plotly_chart(fig3, use_container_width=True)


with tab4:
    st.subheader("Parámetros usados en la simulación")
    st.json({
        "Fa0": Fa0,
        "Fb0": Fb0,
        "Fm0": Fm0,
        "T0": T0,
        "Ta1": Ta1,
        "UA": UA,
        "mc": mc,
        "V": V })


