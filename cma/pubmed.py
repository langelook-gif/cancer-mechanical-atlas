import time, requests, xml.etree.ElementTree as ET
from typing import List, Dict
from .models import Paper
EUTILS="https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def _common(tool,email,api_key=None):
    p={"tool":tool,"email":email}
    if api_key: p["api_key"]=api_key
    return p

def build_query(cancer_type, extra_terms=""):
    mechanics='("Young modulus"[Title/Abstract] OR "Young\'s modulus"[Title/Abstract] OR stiffness[Title/Abstract] OR elasticity[Title/Abstract] OR viscoelastic*[Title/Abstract] OR mechanobiology[Title/Abstract] OR "cell mechanics"[Title/Abstract] OR "nuclear mechanics"[Title/Abstract] OR "cell deformation"[Title/Abstract] OR "atomic force microscopy"[Title/Abstract] OR AFM[Title/Abstract])'
    q=f'("{cancer_type}"[Title/Abstract]) AND {mechanics}'
    return f"{q} AND ({extra_terms})" if extra_terms.strip() else q

def search_pubmed(query,email,tool="cancer_mechanical_atlas",api_key=None,retmax=100,sort="relevance"):
    p=_common(tool,email,api_key); p.update({"db":"pubmed","term":query,"retmode":"json","retmax":str(retmax),"sort":sort})
    r=requests.get(f"{EUTILS}/esearch.fcgi",params=p,timeout=30); r.raise_for_status()
    return r.json().get("esearchresult",{}).get("idlist",[])

def fetch_pubmed(pmids:List[str],email,tool="cancer_mechanical_atlas",api_key=None,batch_size=100):
    out=[]
    for start in range(0,len(pmids),batch_size):
        batch=pmids[start:start+batch_size]
        p=_common(tool,email,api_key); p.update({"db":"pubmed","id":",".join(batch),"retmode":"xml"})
        r=requests.get(f"{EUTILS}/efetch.fcgi",params=p,timeout=45); r.raise_for_status()
        root=ET.fromstring(r.text)
        for article in root.findall('.//PubmedArticle'):
            medline=article.find('MedlineCitation'); art=medline.find('Article') if medline is not None else None
            if art is None: continue
            pmid=medline.findtext('PMID',default='')
            title=''.join(art.find('ArticleTitle').itertext()) if art.find('ArticleTitle') is not None else ''
            abstract=[]
            for node in art.findall('.//Abstract/AbstractText'):
                label=node.attrib.get('Label',''); txt=''.join(node.itertext()).strip()
                if txt: abstract.append(f"{label}: {txt}" if label else txt)
            journal=art.findtext('.//Journal/Title',default='')
            year_txt=art.findtext('.//JournalIssue/PubDate/Year') or art.findtext('.//ArticleDate/Year') or ''
            try: year=int(year_txt)
            except: year=None
            authors=[]
            for a in art.findall('.//AuthorList/Author'):
                last=a.findtext('LastName',default=''); ini=a.findtext('Initials',default='')
                if last: authors.append(f"{last} {ini}".strip())
            doi=''
            for eid in article.findall('.//PubmedData/ArticleIdList/ArticleId'):
                if eid.attrib.get('IdType')=='doi': doi=(eid.text or '').strip(); break
            out.append(Paper(pmid,title,'\n'.join(abstract),journal,year,doi,', '.join(authors)))
        time.sleep(0.12 if api_key else 0.35)
    return out
