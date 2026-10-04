"""Append hand-annotated rows for one region to data/regions_curated/v1_provenance.csv.
Usage: python v1_provenance_append.py <region> <annotation.txt>
Line format (| separated, 12 fields after the video_id is validated against the manifest):
 video_id|province|county_or_area|ethnic_group|singer|singer_inheritor|tier|evidence|pt|dating|label_concern|content_concern
 pt: Y=原生态 F=field M=民族唱法 I=instrumental O=other ; dating: t=traditional k=check c=composed
Skips the region if it already has rows."""
import sys, os, csv
import pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = f'{ROOT}/data/regions_curated/v1_provenance.csv'
COLS = ['region','video_id','province','county_or_area','ethnic_group','singer','singer_inheritor','provenance_tier','provenance_evidence','performance_type_v2','dating_flag','label_concern','content_concern']
PT = dict(Y='原生态', F='field', M='民族唱法', I='instrumental', O='other')
DT = dict(t='traditional', k='check', c='composed')
reg, f = sys.argv[1], sys.argv[2]
m = pd.read_csv(f'{ROOT}/data/regions_audio/manifest.csv'); m = m[(m.status=='ok')&(m.region==reg)]
if os.path.exists(OUT) and (pd.read_csv(OUT).region == reg).any():
    print('region already present, skipping'); sys.exit()
rows = {}
for ln in open(f, encoding='utf8'):
    ln = ln.rstrip('\n')
    if not ln.strip(): continue
    p = [x.strip() for x in ln.split('|')]
    assert len(p) == 12, (len(p), ln[:60])
    vid = p[0]
    assert vid in set(m.video_id) and vid not in rows, vid
    assert p[6] in ('A','B','C') and p[8] in PT and p[9] in DT, ln[:60]
    rows[vid] = [reg, vid, p[1], p[2], p[3], p[4], p[5], p[6], p[7], PT[p[8]], DT[p[9]], p[10], p[11]]
missing = set(m.video_id) - set(rows)
assert not missing, f'missing {missing}'
new = not os.path.exists(OUT)
with open(OUT, 'a', newline='', encoding='utf8') as fh:
    w = csv.writer(fh)
    if new: w.writerow(COLS)
    for v in m.video_id: w.writerow(rows[v])
print('appended', len(rows))
