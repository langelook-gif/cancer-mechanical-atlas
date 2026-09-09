import numpy as np
EPS=1e-30

def forced_oscillator_response(freq_hz,fn_hz,zeta):
    r=np.asarray(freq_hz,float)/np.maximum(np.asarray(fn_hz,float),EPS)
    return 1/np.sqrt((1-r**2)**2+(2*zeta*r)**2+EPS)

def proxy_natural_frequency(E_pa,radius_m,density=1050.0,stiffness_factor=6*np.pi):
    """Exploratory proxy only: k~C*E*r, m~rho*4/3*pi*r^3, fn=(1/2pi)sqrt(k/m). Not a validated cell-ablation model."""
    E=np.asarray(E_pa,float); r=np.asarray(radius_m,float)
    k=stiffness_factor*E*r; m=density*(4/3)*np.pi*r**3
    return (1/(2*np.pi))*np.sqrt(np.maximum(k,EPS)/np.maximum(m,EPS))

def sample_lognormal_from_median_iqr(median,q25,q75,n,rng):
    vals=np.array([q25,median,q75],float)
    if np.any(vals<=0):
        sd=max((q75-q25)/1.349,abs(median)*.1,EPS); return np.maximum(rng.normal(median,sd,n),EPS)
    sigma=(np.log(q75)-np.log(q25))/1.349; return rng.lognormal(np.log(median),max(sigma,1e-4),n)

def monte_carlo_frequency_hypothesis(cancer_E,healthy_E,cancer_radius,healthy_radius,n=5000,seed=42,zeta_cancer=.10,zeta_healthy=.08,fmin_hz=1e3,fmax_hz=1e6,nfreq=800):
    rng=np.random.default_rng(seed)
    cE=sample_lognormal_from_median_iqr(*cancer_E,n=n,rng=rng); hE=sample_lognormal_from_median_iqr(*healthy_E,n=n,rng=rng)
    cr=sample_lognormal_from_median_iqr(*cancer_radius,n=n,rng=rng); hr=sample_lognormal_from_median_iqr(*healthy_radius,n=n,rng=rng)
    cfn=proxy_natural_frequency(cE,cr); hfn=proxy_natural_frequency(hE,hr)
    freq=np.logspace(np.log10(fmin_hz),np.log10(fmax_hz),nfreq)
    c=np.mean(forced_oscillator_response(freq[None,:],cfn[:,None],zeta_cancer),axis=0); h=np.mean(forced_oscillator_response(freq[None,:],hfn[:,None],zeta_healthy),axis=0)
    c/=max(c.max(),EPS); h/=max(h.max(),EPS); sel=c/np.maximum(h,1e-6); useful=c>=.30
    idx=int(np.argmax(np.where(useful,sel,-np.inf))) if useful.any() else int(np.argmax(c-h))
    return {'frequency_hz':freq,'cancer_response':c,'healthy_response':h,'selectivity':sel,'best_index':idx,'best_frequency_hz':float(freq[idx]),'best_selectivity':float(sel[idx]),'cancer_fn_hz':cfn,'healthy_fn_hz':hfn}
