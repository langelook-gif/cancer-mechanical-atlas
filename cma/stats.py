import numpy as np, pandas as pd
from scipy.stats import gaussian_kde

def cohen_d(a,b):
    a=np.asarray(a,float); b=np.asarray(b,float)
    if len(a)<2 or len(b)<2: return np.nan
    pooled=np.sqrt(((len(a)-1)*np.var(a,ddof=1)+(len(b)-1)*np.var(b,ddof=1))/(len(a)+len(b)-2))
    return np.nan if pooled==0 else (np.mean(a)-np.mean(b))/pooled

def overlap_coefficient(a,b,gridsize=512):
    a=np.asarray(a,float); b=np.asarray(b,float)
    if len(a)<3 or len(b)<3: return np.nan
    lo=min(a.min(),b.min()); hi=max(a.max(),b.max())
    if hi<=lo: return np.nan
    grid=np.linspace(lo,hi,gridsize)
    try:
        ka=gaussian_kde(a)(grid); kb=gaussian_kde(b)(grid)
        return float(np.clip(np.trapezoid(np.minimum(ka,kb),grid),0,1))
    except: return np.nan

def summarize_property(df,prop):
    d=df[df.property_name==prop]; rows=[]
    for label in ['cancer','healthy']:
        x=d.loc[d.cohort_label==label,'normalized_value'].dropna().to_numpy(float)
        if len(x): rows.append({'cohort':label,'n':len(x),'median':float(np.median(x)),'q25':float(np.quantile(x,.25)),'q75':float(np.quantile(x,.75)),'mean':float(np.mean(x))})
    return pd.DataFrame(rows)

def separability(df,prop):
    d=df[df.property_name==prop]
    c=d.loc[d.cohort_label=='cancer','normalized_value'].dropna().to_numpy(float)
    h=d.loc[d.cohort_label=='healthy','normalized_value'].dropna().to_numpy(float)
    return {'property':prop,'n_cancer':len(c),'n_healthy':len(h),'cohen_d':cohen_d(c,h),'overlap_coefficient':overlap_coefficient(c,h)}
