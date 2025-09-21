import numpy as np
import streamlit as st
from scipy.integrate import solve_ivp
import plotly.graph_objects as go

R = 1.987  # cal/mol-K

# --- Perfiles posibles de mc ---
def mc_step(t, mc0, mc1, t_step, t_end):
    if t < t_step:
        return mc0
    elif t_step <= t <= t_end:
        return mc1 #+ (mc1 - mc0) * (t - t_step) / (t_end - t_step)
    else:
        return mc0


def mc_rampa(t, mc0, mc1, t_step, t_end):
    if t < t_step:
        return mc0
    elif t_step <= t <= t_end:
        return mc0 + (mc1 - mc0) * (t - t_step) / (t_end - t_step)
    else:
        return mc1

def mc_exp(t, mc0, mc1, t_step, tau=1.0):
    """Crecimiento exponencial hacia mc1 a partir de t_step con constante de tiempo tau"""
    if t < t_step:
        return mc0
    else:
        return mc1 - (mc1 - mc0) * np.exp(-(t - t_step)/tau)

# --- ODEs ---
def cstr_odes(t, y, Fa0, Fb0, Fm0, V, UA, Ta1, T0,
              mc0, mc1, t_step, t_end, perfil, tau_exp):
    Ca, Cb, Cc, Cm, T = y
    
    # cinética
    k = 16.96e12 * np.exp(-32400 / (R * (T + 460)))
    ra = -k * Ca
    rb = -k * Ca
    rc = k * Ca
    rm = 0.0

    # balances de masa
    v0 = Fa0/0.923 + Fb0/3.45 + Fm0/1.54
    tau = V / v0
    Ca0, Cb0, Cm0 = Fa0/v0, Fb0/v0, Fm0/v0

    dCa_dt = (Ca0 - Ca)/tau + ra
    dCb_dt = (Cb0 - Cb)/tau + rb
    dCc_dt = (0.0 - Cc)/tau + rc
    dCm_dt = (Cm0 - Cm)/tau + rm

    # elegir perfil de mc
    if perfil == "Step":
        mc_t = mc_step(t, mc0, mc1, t_step, t_end)
    elif perfil == "Rampa lineal":
        mc_t = mc_rampa(t, mc0, mc1, t_step, t_end)
    elif perfil == "Exponencial":
        mc_t = mc_exp(t, mc0, mc1, t_step, tau_exp)
    else:
        mc_t = mc0

    # balance de energía
    ThetaCp = 35 + Fb0/Fa0*18 + Fm0/Fa0*19.5
    Q = mc_t * 18 * (Ta1 - (T - (T - Ta1) * np.exp(-UA/(18*mc_t))))
    NCp = Ca*V*35 + Cb*V*18 + Cc*V*46 + Cm*V*19.5
    dT_dt = (Q - Fa0*ThetaCp*(T - T0) + (-36000)*ra*V) / (NCp + 1e-8)

    return [dCa_dt, dCb_dt, dCc_dt, dCm_dt, dT_dt]

# --- Interfaz Streamlit ---
st.set_page_config(page_title="Simulador TAC con perfiles mc(t)", layout="wide")
st.title("Arranque de Reactor TAC - Perfiles dinámicos de refrigerante")

Fa0 = 80 
Fb0 = 1000 
Fm0 = 100
V = (1/7.484)*500 
UA  = 16000
Ta1 = 60 
T0  = 75 


st.sidebar.header("Perfil temporal del refrigerante")
perfil = st.sidebar.selectbox("Seleccionar perfil", ["Step", "Rampa lineal", "Exponencial"])
mc0    = st.sidebar.slider("mc0 (inicial) [kg/min]", 500, 5000, 1000, 100)
mc1    = st.sidebar.slider("mc1 (final) [kg/min]", 500, 5000, 2000, 100)
t_step = st.sidebar.slider("t_step (min)", 0.0, 10.0, 1.0, 0.1)
t_end  = st.sidebar.slider("t_end (min)", 0.0, 10.0, 3.0, 0.1)
tau_exp = st.sidebar.slider("Tau exp (min)", 0.1, 5.0, 1.0, 0.1)

# condiciones iniciales
y0 = [0.0, 3.45, 0.0, 0.0, T0]
t_span = (0, 4)
t_eval = np.linspace(0, 4, 300)


sol = solve_ivp(cstr_odes, t_span, y0, t_eval=t_eval, method="BDF",
                args=(Fa0, Fb0, Fm0, V, UA, Ta1, T0,
                      mc0, mc1, t_step, t_end, perfil, tau_exp))

mc_vals = []
for ti in sol.t:
    if perfil == "Step":
        mc_vals.append(mc_step(ti, mc0, mc1, t_step, t_end))
    elif perfil == "Rampa lineal":
        mc_vals.append(mc_rampa(ti, mc0, mc1, t_step, t_end))
    elif perfil == "Exponencial":
        mc_vals.append(mc_exp(ti, mc0, mc1, t_step, tau_exp))
    else:
        mc_vals.append(mc0)

fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=sol.t, y=sol.y[0], mode="lines", name="Ca"))
fig1.add_trace(go.Scatter(x=sol.t, y=sol.y[4], mode="lines", name="T", yaxis="y2"))

fig1.update_layout(
    xaxis=dict(title="Tiempo [min]"),
    yaxis=dict(title="Concentraciones [mol/L]"),
    yaxis2=dict(title="Temperatura [K]", overlaying="y", side="right"),
    title=f"Simulación con perfil dinámico de mc(t): {perfil}"
)

st.plotly_chart(fig1, use_container_width=True)

fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=sol.t, y=mc_vals, mode="lines", name="mc(t)"))
fig2.update_layout(
    xaxis=dict(title="Tiempo [min]"),
    yaxis=dict(title="mc(t) [kg/min]"),
    title="Perfil temporal del refrigerante"
)
st.plotly_chart(fig2, use_container_width=True)
