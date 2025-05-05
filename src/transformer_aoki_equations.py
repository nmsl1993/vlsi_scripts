# Design a transformer model to using the Aoki equations

import numpy as np
import skrf as rf

RL = 10.2
Q1 = 7
Q2 = 7
CL = 103e-15
f = 5.8e9
w = 2*np.pi*f
#L1=954e-12
n=1
L2 = 1/(w**2.0*CL)
L1 = L2/n**2.0
print(f'L1: {L1} L2: {L2}')
k = 0.7
# Calculate the inductance of the transformer
L = RL * Q1 * Q2 * CL

eta = (
    (RL / n**2.0) / 
    ((w*L1/Q2 + RL/n**2.0)/(w*k*L1)**2.0 * w*L1/Q1 + w*L1/Q2 + RL/n**2.0)
)
print(eta)
print(10.0*np.log10(eta))