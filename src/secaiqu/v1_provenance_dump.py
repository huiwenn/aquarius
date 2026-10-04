"""Compact per-region dump of v1 items for provenance annotation.
Usage: python v1_provenance_dump.py <region-index 0..14 | region name> [desc_chars]
"""
import sys, json, os
import pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
m = pd.read_csv(f'{ROOT}/data/regions_audio/manifest.csv')
m = m[m.status == 'ok']
regions = list(dict.fromkeys(m.region))
arg = sys.argv[1]
reg = regions[int(arg)] if arg.isdigit() else arg
n = int(sys.argv[2]) if len(sys.argv) > 2 else 600
if arg == 'list':
    print(regions); sys.exit()
for _, r in m[m.region == reg].iterrows():
    p = f"{ROOT}/data/regions_audio/{reg}/{r.video_id}.info.json"
    d = {}
    if os.path.exists(p):
        d = json.load(open(p))
    desc = (d.get('description') or '').replace('\n', ' / ')[:n]
    tags = ','.join((d.get('tags') or [])[:8])
    print(f"## {r.video_id} | {r.title} | ch={r.channel} | song={r.song_name} | pa={r.province_or_area} | genre={r.genre} | pt={r.performance_type} | eth={r.ethnic_group} | note={r.note}")
    print(f"   desc: {desc}\n   tags: {tags}")
# song-date lookup for non-traditional songs of this region
d = pd.read_csv(f'{ROOT}/data/regions_curated/song_dates/all_songs.csv')
x = d[(d.region == reg) & (~d.song_type.fillna('').eq('traditional'))]
print('\n# non-traditional in all_songs.csv for region:')
for _, r in x.iterrows():
    print(f"  {r.song_name} | {r.song_type} | {r.composer_or_adapter} | {r.date_best}")
