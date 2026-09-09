import numpy as np
from cma.physics import proxy_natural_frequency, forced_oscillator_response

def test_frequency_positive():
    f=proxy_natural_frequency(1000.0,10e-6); assert np.isfinite(f) and f>0

def test_resonance_peak():
    fn=100000.; freq=np.array([50000.,100000.,200000.]); r=forced_oscillator_response(freq,fn,.1); assert r[1]>r[0] and r[1]>r[2]
