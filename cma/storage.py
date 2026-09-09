import sqlite3, pandas as pd
SCHEMA='''
CREATE TABLE IF NOT EXISTS papers (pmid TEXT PRIMARY KEY,title TEXT,abstract TEXT,journal TEXT,year INTEGER,doi TEXT,authors TEXT,source TEXT);
CREATE TABLE IF NOT EXISTS measurements (id INTEGER PRIMARY KEY AUTOINCREMENT,pmid TEXT,title TEXT,cancer_type TEXT,tissue_context TEXT,cohort_label TEXT,property_name TEXT,value REAL,unit TEXT,normalized_value REAL,normalized_unit TEXT,measurement_method TEXT,context_snippet TEXT,evidence_level TEXT,extraction_confidence REAL,notes TEXT);
'''
def connect(path='cancer_mechanical_atlas.sqlite'):
    c=sqlite3.connect(path); c.executescript(SCHEMA); return c
def save_papers(conn,papers):
    rows=[p.to_dict() for p in papers]
    if not rows:return
    cols=['pmid','title','abstract','journal','year','doi','authors','source']; q=','.join(['?']*len(cols))
    conn.executemany(f"INSERT OR REPLACE INTO papers ({','.join(cols)}) VALUES ({q})",[[r.get(c) for c in cols] for r in rows]); conn.commit()
def save_measurements(conn,ms):
    rows=[m.to_dict() for m in ms]
    if not rows:return
    cols=['pmid','title','cancer_type','tissue_context','cohort_label','property_name','value','unit','normalized_value','normalized_unit','measurement_method','context_snippet','evidence_level','extraction_confidence','notes']; q=','.join(['?']*len(cols))
    conn.executemany(f"INSERT INTO measurements ({','.join(cols)}) VALUES ({q})",[[r.get(c) for c in cols] for r in rows]); conn.commit()
def load_papers(conn): return pd.read_sql_query('SELECT * FROM papers ORDER BY year DESC',conn)
def load_measurements(conn): return pd.read_sql_query('SELECT * FROM measurements ORDER BY id DESC',conn)
def replace_measurements_from_df(conn,df):
    conn.execute('DELETE FROM measurements'); conn.commit(); cols=['pmid','title','cancer_type','tissue_context','cohort_label','property_name','value','unit','normalized_value','normalized_unit','measurement_method','context_snippet','evidence_level','extraction_confidence','notes']
    d=df.copy(); [d.__setitem__(c,None) for c in cols if c not in d.columns]; d[cols].to_sql('measurements',conn,if_exists='append',index=False)
