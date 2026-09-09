import re
from .models import Measurement
SPACE=r"(?:\s|[\u00A0\u202F])*"
UNIT_MAP={"pa":("Pa",1.0),"kpa":("Pa",1e3),"mpa":("Pa",1e6),"gpa":("Pa",1e9),"nm":("m",1e-9),"µm":("m",1e-6),"μm":("m",1e-6),"um":("m",1e-6),"mm":("m",1e-3)}
MECH_TERMS={
 "youngs_modulus":[r"young'?s?\s+modulus",r"elastic\s+modulus",r"effective\s+modulus"],
 "stiffness":[r"cell(?:ular)?\s+stiffness",r"stiffness",r"elasticity"],
 "cell_radius":[r"cell\s+radius"],"cell_diameter":[r"cell\s+diameter",r"diameter\s+of\s+(?:the\s+)?cells?"],
 "nucleus_radius":[r"nucle(?:us|ar)\s+radius"],"nucleus_diameter":[r"nucle(?:us|ar)\s+diameter"]}
METHOD_TERMS={"AFM":[r"atomic force microscopy",r"\bAFM\b"],"micropipette aspiration":[r"micropipette aspiration"],"optical stretcher":[r"optical stretcher"],"indentation":[r"indentation"],"magnetic twisting cytometry":[r"magnetic twisting cytometry"],"Brillouin microscopy":[r"Brillouin"]}
CANCER_MARKERS=["cancer","tumor","tumour","malignant","glioblastoma","gbm","carcinoma","melanoma","leukemia","lymphoma","sarcoma"]
HEALTHY_MARKERS=["healthy","normal","non-cancer","noncancer","benign","control","non-malignant","nonmalignant"]

def _method(text):
    for label,pats in METHOD_TERMS.items():
        if any(re.search(p,text,re.I) for p in pats): return label
    return ""
def _cohort(snippet):
    s=snippet.lower(); c=sum(k in s for k in CANCER_MARKERS); h=sum(k in s for k in HEALTHY_MARKERS)
    return "cancer" if c>h else "healthy" if h>c else "unspecified"
def _snippet(text,start,end,window=240): return re.sub(r"\s+"," ",text[max(0,start-window):min(len(text),end+window)]).strip()
def _normalize(value,unit):
    key=unit.lower().replace("μ","µ")
    if key not in UNIT_MAP: return value,unit
    out,m=UNIT_MAP[key]; return value*m,out

def extract_measurements(paper,cancer_type):
    text=f"{paper.title}. {paper.abstract}"; out=[]
    for prop,terms in MECH_TERMS.items():
        term='(?:'+'|'.join(terms)+')'
        patterns=[
            re.compile(rf"(?P<term>{term}).{{0,120}}?(?P<value>\d+(?:\.\d+)?){SPACE}(?P<unit>GPa|MPa|kPa|Pa|mm|µm|μm|um|nm)\b",re.I|re.S),
            re.compile(rf"(?P<value>\d+(?:\.\d+)?){SPACE}(?P<unit>GPa|MPa|kPa|Pa|mm|µm|μm|um|nm)\b.{{0,80}}?(?P<term>{term})",re.I|re.S)]
        for pat in patterns:
            for m in pat.finditer(text):
                v=float(m.group('value')); u=m.group('unit'); nv,nu=_normalize(v,u); sn=_snippet(text,m.start(),m.end()); method=_method(sn); cohort=_cohort(sn)
                conf=.45 + (.15 if method else 0) + (.15 if cohort!='unspecified' else 0) + (.10 if re.search(r'\b(mean|median|measured|was|were|of)\b',sn,re.I) else 0)
                out.append(Measurement(paper.pmid,paper.title,cancer_type,"",cohort,prop,v,u,nv,nu,method,sn,"abstract_extracted",min(conf,.90),"Machine-extracted; verify in original paper."))
    seen=set(); ded=[]
    for m in out:
        k=(m.pmid,m.property_name,round(m.normalized_value,12),m.normalized_unit,m.cohort_label)
        if k not in seen: seen.add(k); ded.append(m)
    return ded
