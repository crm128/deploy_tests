import numpy as np


R = 1.987

def cstr_odes(t, y, Fa0, Fb0, Fm0, V, UA, Ta1, mc, T0):
    Ca, Cb, Cc, Cm, T = y
    
    k = 16.96e12 * np.exp(-32400 / (R * (T + 460)))
    ra = -k * Ca
    rb = -k * Ca
    rc = k * Ca
    rm = 0.0
    
    v0 = Fa0/0.923 + Fb0/3.45 + Fm0/1.54
    tau = V / v0
    
    Ca0 = Fa0 / v0
    Cb0 = Fb0 / v0
    Cm0 = Fm0 / v0
    
    dCa_dt = (Ca0 - Ca)/tau + ra
    dCb_dt = (Cb0 - Cb)/tau + rb
    dCc_dt = (0.0 - Cc)/tau + rc
    dCm_dt = (Cm0 - Cm)/tau + rm
    
    ThetaCp = 35 + Fb0/Fa0*18 + Fm0/Fa0*19.5
    Q = mc * 18 * (Ta1 - (T - (T - Ta1) * np.exp(-UA/(18*mc))))
    NCp = Ca*V*35 + Cb*V*18 + Cc*V*46 + Cm*V*19.5
    dT_dt = (Q - Fa0*ThetaCp*(T - T0) + (-36000)*ra*V) / (NCp + 1e-8)
    
    return [dCa_dt, dCb_dt, dCc_dt, dCm_dt, dT_dt]
