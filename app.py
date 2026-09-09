import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from cma.pubmed import build_query, search_pubmed, fetch_pubmed
from cma.extract import extract_measurements
from cma.storage import connect, save_papers, save_measurements, load_papers, load_measurements, replace_measurements_from_df
from cma.stats import summarize_property, separability
from cma.physics import monte_carlo_frequency_hypothesis
from cma.verified_seed import load_verified_studies, seed_verified_measurements

st.set_page_config(page_title="Cancer Mechanical Atlas",page_icon="🧬",layout="wide")
conn=connect('cancer_mechanical_atlas.sqlite')
seed_verified_measurements(conn)
st.title('Cancer Mechanical Atlas')
st.caption('Literature-grounded mechanobiology evidence → cancer-vs-healthy comparison → exploratory acoustic-response hypotheses.')
st.warning('Research-use only. This app does not identify a treatment frequency, safe dose, or clinical ultrasound protocol. Every machine-extracted value must be verified against the original paper before it is used as evidence.')

with st.sidebar:
    st.header('Project')
    cancer_type=st.text_input('Cancer type',value='glioblastoma')
    email=st.text_input('Email for NCBI E-utilities',value=os.getenv('NCBI_EMAIL',''),help='NCBI asks API users to include a valid email and tool name.')
    api_key=st.text_input('NCBI API key (optional)',value=os.getenv('NCBI_API_KEY',''),type='password')
    st.divider()
    st.markdown('**Evidence rule**\n\nMachine extraction is a lead, not a fact. Promote values to `verified` only after opening the paper and checking the exact measurement.')

tabs=st.tabs(['1 · Literature Search','2 · Evidence Curator','3 · Mechanical Atlas','4 · Frequency Hypothesis','5 · Method & Limits'])

with tabs[0]:
    st.subheader('Search PubMed for mechanobiology evidence')
    c1,c2=st.columns([2,1])
    with c1:
        extra_terms=st.text_input('Optional extra PubMed terms',value='',placeholder='e.g. ("normal astrocytes" OR astrocyte)')
    with c2:
        retmax=st.number_input('Maximum papers',min_value=5,max_value=500,value=80,step=5)
    query=build_query(cancer_type,extra_terms); st.code(query,language='text')
    if st.button('Search + extract candidate measurements',type='primary'):
        if not email.strip(): st.error('Enter an email address for NCBI E-utilities.')
        else:
            with st.spinner('Searching PubMed and reading abstracts...'):
                try:
                    pmids=search_pubmed(query,email.strip(),api_key=api_key.strip() or None,retmax=int(retmax))
                    papers=fetch_pubmed(pmids,email.strip(),api_key=api_key.strip() or None)
                    save_papers(conn,papers)
                    ms=[]
                    for p in papers: ms.extend(extract_measurements(p,cancer_type))
                    save_measurements(conn,ms)
                    st.success(f'Fetched {len(papers)} papers and extracted {len(ms)} candidate measurements.')
                except Exception as e: st.exception(e)
verified_studies = load_verified_studies()

st.subheader('Verified GBM starter literature')

st.write(
    f'{len(verified_studies)} manually verified studies are bundled with this project.'
)

st.dataframe(
    verified_studies[
        [
            'pmid',
            'year',
            'title',
            'journal',
            'study_type',
            'bottom_line',
            'evidence_direction',
            'verification_status',
            'source_url'
        ]
    ],
    use_container_width=True,
    hide_index=True
)
papers_df=load_papers(conn)
if len(papers_df):
    st.metric('Papers in local evidence store',len(papers_df))
    show=papers_df[['pmid','year','title','journal','doi']].copy(); show['PubMed']=show['pmid'].map(lambda x:f'https://pubmed.ncbi.nlm.nih.gov/{x}/')
    st.dataframe(show,use_container_width=True,hide_index=True)
else: st.info('No papers stored yet.')

with tabs[1]:
    st.subheader('Human-in-the-loop evidence curation')
    mdf=load_measurements(conn)
    if mdf.empty: st.info('Run a literature search first.')
    else:
        st.write('Edit cohort labels, methods, notes, or evidence level here. A machine-extracted value should become `verified` only after you check the original paper.')
        cols=['id','pmid','cancer_type','cohort_label','property_name','value','unit','normalized_value','normalized_unit','measurement_method','extraction_confidence','evidence_level','context_snippet','notes']
        edited=st.data_editor(mdf[cols].copy(),use_container_width=True,hide_index=True,disabled=['id','pmid','property_name','value','unit','normalized_value','normalized_unit','context_snippet'],column_config={
            'cohort_label':st.column_config.SelectboxColumn(options=['cancer','healthy','unspecified']),
            'evidence_level':st.column_config.SelectboxColumn(options=['abstract_extracted','fulltext_extracted','verified','excluded']),
            'extraction_confidence':st.column_config.NumberColumn(min_value=0.,max_value=1.,step=.05)})
        if st.button('Save curation edits'):
            merged=mdf.copy().set_index('id'); e=edited.set_index('id')
            for col in ['cancer_type','cohort_label','measurement_method','extraction_confidence','evidence_level','notes']: merged.loc[e.index,col]=e[col]
            replace_measurements_from_df(conn,merged.reset_index()); st.success('Saved.')
        st.download_button('Download evidence CSV',mdf.to_csv(index=False).encode('utf-8'),file_name='mechanical_evidence.csv',mime='text/csv')

with tabs[2]:
    st.subheader('Cancer vs healthy mechanical evidence')
    mdf=load_measurements(conn)
    if mdf.empty: st.info('No extracted evidence yet.')
    else:
        include_machine=st.checkbox('Include unverified machine-extracted values',value=True,help='Turn this off for a conservative analysis after you have verified papers.')
        d=mdf.copy() if include_machine else mdf[mdf.evidence_level=='verified'].copy()
        d=d[d.cohort_label.isin(['cancer','healthy'])]; props=sorted(d.property_name.dropna().unique().tolist())
        if not props: st.warning('No cancer-vs-healthy labeled measurements available.')
        else:
            prop=st.selectbox('Mechanical property',props); summ=summarize_property(d,prop); sep=separability(d,prop)
            a,b,c=st.columns(3); a.metric('Cancer measurements',sep['n_cancer']); b.metric('Healthy measurements',sep['n_healthy']); ov=sep['overlap_coefficient']; c.metric('Estimated distribution overlap','n/a' if pd.isna(ov) else f'{ov:.2f}')
            st.dataframe(summ,use_container_width=True,hide_index=True)
            fig=go.Figure()
            for label in ['cancer','healthy']:
                vals=d.loc[(d.property_name==prop)&(d.cohort_label==label),'normalized_value'].dropna()
                if len(vals): fig.add_trace(go.Histogram(x=vals,name=label,opacity=.55,histnorm='probability density'))
            fig.update_layout(barmode='overlay',title=f'{prop}: cancer vs healthy',xaxis_title='Normalized value',yaxis_title='Density'); st.plotly_chart(fig,use_container_width=True)
            st.caption('Low overlap supports mechanical separability; high overlap argues against using this property by itself. These distributions are only as trustworthy as the curated evidence.')

with tabs[3]:
    st.subheader('Exploratory frequency-response hypothesis')
    st.error('This module is intentionally a hypothesis generator, not a treatment calculator. It uses a simplified oscillator proxy and should not be used for experimental dosing or clinical decisions.')
    mdf=load_measurements(conn); verified_only=st.checkbox('Use verified evidence only',value=False,key='freq_verified'); d=mdf.copy()
    if verified_only: d=d[d.evidence_level=='verified']
    d=d[d.cohort_label.isin(['cancer','healthy'])]
    def triplet(prop,cohort):
        vals=d.loc[(d.property_name==prop)&(d.cohort_label==cohort),'normalized_value'].dropna().to_numpy(float)
        if len(vals)<1:return None
        return (float(np.median(vals)),float(np.quantile(vals,.25)),float(np.quantile(vals,.75)))
    cE=triplet('youngs_modulus','cancer'); hE=triplet('youngs_modulus','healthy')
    def radius_triplet(cohort):
        r=triplet('cell_radius',cohort)
        if r:return r
        dia=triplet('cell_diameter',cohort); return tuple(v/2 for v in dia) if dia else None
    cr=radius_triplet('cancer'); hr=radius_triplet('healthy')
    if not all([cE,hE,cr,hr]):
        st.warning("The model needs cancer + healthy Young's modulus and cell radius/diameter evidence. Collect and verify those measurements first.")
        st.write({'cancer_E':cE,'healthy_E':hE,'cancer_radius':cr,'healthy_radius':hr})
    else:
        st.write('Evidence summaries used by the model:'); st.json({'cancer_Youngs_modulus_Pa_(median,q25,q75)':cE,'healthy_Youngs_modulus_Pa_(median,q25,q75)':hE,'cancer_radius_m_(median,q25,q75)':cr,'healthy_radius_m_(median,q25,q75)':hr})
        c1,c2,c3=st.columns(3); n_mc=c1.number_input('Monte Carlo cells / group',500,20000,5000,500); fmin_khz=c2.number_input('Plot min frequency (kHz)',1.,500.,1.,1.); fmax_khz=c3.number_input('Plot max frequency (kHz)',10.,3000.,1000.,10.)
        if st.button('Run exploratory frequency model'):
            result=monte_carlo_frequency_hypothesis(cE,hE,cr,hr,n=int(n_mc),fmin_hz=fmin_khz*1e3,fmax_hz=fmax_khz*1e3); best=result['best_frequency_hz']/1e3
            a,b=st.columns(2); a.metric('Exploratory modeled frequency',f'{best:.1f} kHz'); b.metric('Modeled cancer/healthy response ratio',f"{result['best_selectivity']:.2f}×")
            fig=go.Figure(); fig.add_trace(go.Scatter(x=result['frequency_hz']/1e3,y=result['cancer_response'],mode='lines',name='Cancer modeled response')); fig.add_trace(go.Scatter(x=result['frequency_hz']/1e3,y=result['healthy_response'],mode='lines',name='Healthy modeled response')); fig.add_vline(x=best,line_dash='dash'); fig.update_xaxes(type='log',title='Frequency (kHz)'); fig.update_yaxes(title='Normalized modeled response'); fig.update_layout(title='Exploratory frequency-response comparison'); st.plotly_chart(fig,use_container_width=True)
            st.caption('This is the frequency where this simplified proxy predicts a useful cancer-vs-healthy response difference given the current evidence. It is not a validated cell resonance, therapeutic setting, or injury threshold.')

with tabs[4]:
    st.subheader('How this system should be used')
    st.markdown('''
### Pipeline
1. **Retrieve** mechanobiology papers from PubMed.
2. **Extract candidate measurements** from titles/abstracts.
3. **Human-verify** every important number against the original paper.
4. **Normalize** units while keeping provenance and measurement method.
5. **Compare distributions** for cancer and matched healthy cells.
6. **Quantify overlap**, rather than comparing only means.
7. **Generate an exploratory physics hypothesis** only when evidence is sufficient.
8. **Test sensitivity and falsification conditions** before any biological experiment.

### What should eventually be added
- Full-text extraction from PMC or publisher-licensed content.
- Measurement-method harmonization (AFM vs indentation vs optical stretcher).
- Cell line / patient / tissue context ontology.
- Separate nucleus, membrane, cytoplasm and extracellular-matrix evidence.
- Bayesian hierarchical meta-analysis rather than pooling raw values.
- Literature-quality scoring and risk-of-bias review.
- A validated multi-degree-of-freedom cell model.
- Independent experimental datasets for model calibration and falsification.
- CT-derived or experimentally measured acoustic propagation for any transcranial application.

### Non-negotiable scientific rule
The system must be allowed to conclude **“the distributions overlap too much; no useful frequency hypothesis is supported.”** A model that is forced to find a target is not a scientific discovery engine.
''')
