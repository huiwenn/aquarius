# License Audit

All datasets in Aquarius and their redistribution status. This is critical for the TISMIR dataset article: Aquarius cannot redistribute data from datasets that prohibit it.

---

## Redistribution Summary

| Status | Meaning | Datasets |
|--------|---------|----------|
| **Redistributable** | Can include data in Aquarius release | POP909, Kaggle Folk, CCOM-HuQin, Jingju Singing |
| **Metadata-only** | Can reference but not redistribute raw data | CCMusic ecosystem, M4Singer, GTSinger, PMEmo, ACE-OpenCpop |
| **Unclear** | License not specified; need to contact authors | ChMusic, Guqin, Anthology, MGD |

---

## Per-Dataset License Details

| # | Dataset | License | Redistributable? | Notes |
|---|---------|---------|-------------------|-------|
| 1 | POP909 | MIT | **Yes** | Open, unrestricted |
| 2 | ChMusic | MIT (repo) | **Likely yes** | Repo is MIT but audio provenance unclear; verify with authors |
| 3 | Guqin Dataset | Unspecified | **Unclear** | No LICENSE file in repo; contact author (Wu Yusong) |
| 4 | Anthology of Chinese Folk Songs | Unspecified | **Unclear** | Original jianpu scans are copyrighted; MIDI/MusicXML derived status uncertain |
| 5 | PMEmo | Research use | **No** | Emotional music dataset; research-only terms |
| 6 | M4Singer | Custom license | **No** | Free-to-use but redistribution restricted per dataset_license.md |
| 7 | MGD | Unspecified | **Unclear** | No license statement found; 31,761 metadata-only items (no audio) |
| 8 | CTIS | CC-BY-NC-ND-4.0 + CCMusic institutional clause | **No** | CCMusic application terms restrict to applicant's institution only |
| 9 | GZ_IsoTech | CC-BY-4.0 + CCMusic institutional clause | **No** | CCMusic application terms restrict to applicant's institution only |
| 10 | Kaggle Folk | CC0-1.0 | **Yes** | Public domain |
| 11 | Jingju Singing Audio | CC (Zenodo) | **Likely yes** | Check specific CC variant on Zenodo record |
| 12 | CCOM-HuQin | CC-BY-4.0 | **Yes** | No institutional restriction found |
| 13 | CNPM | CC-BY-4.0 + CCMusic institutional clause | **No** | CCMusic application terms restrict to applicant's institution only |
| 14 | ErhuPT | CC-BY-4.0 + CCMusic institutional clause | **No** | CCMusic application terms restrict to applicant's institution only |
| 15 | ACE-OpenCpop | CC-BY-NC-4.0 | **Metadata only** | Derived from Opencpop which requires application; check if ACE extension inherits that restriction |
| 16 | GTSinger | Custom (HuggingFace gated) | **No** | Requires acceptance of terms; redistribution not permitted |

---

## CCMusic Institutional Restriction

**Affects**: CTIS, GZ_IsoTech, CNPM, ErhuPT (and any future CCMusic-ecosystem datasets: GuzhengTech99, XFID, GuzhengMidiWav)

The CCMusic application form includes this clause:

> "2. This database can only be used by the applicant and members of the applicant's department or research institution."

This means:
1. Raw audio/data from these datasets **cannot** be bundled into Aquarius for public distribution
2. Each user of Aquarius must independently apply to CCMusic for access
3. The Aquarius master table can include **metadata pointers** (IDs, labels, schema mappings) but not the underlying recordings
4. The TISMIR article should document this as a "bring your own data" requirement for CCMusic components

**Contact**: ccmusic.database@hotmail.com

---

## Implications for TISMIR Dataset Article

### What Aquarius CAN distribute
- Unified metadata table (master_table.parquet) with all 46,327+ items
- Schema mappings, gap analysis, coverage reports
- Data from MIT/CC0/CC-BY licensed datasets (POP909, Kaggle Folk, CCOM-HuQin)
- Download scripts and loaders (src/unify.py) that users run on their own copies

### What Aquarius CANNOT distribute
- Raw audio from CCMusic ecosystem (CTIS, GZ_IsoTech, CNPM, ErhuPT)
- Raw audio from M4Singer, GTSinger, PMEmo
- Any data from datasets with unspecified licenses (until clarified)

### Recommended approach
Follow the precedent set by datasets like DALI, MusicNet, and Musdb18: distribute the unified metadata and tooling, with clear instructions for users to obtain restricted-license data themselves. The `docs/gated_datasets.md` file already provides this information.

---

## Action Items

1. **Verify Jingju Singing Audio**: Check exact CC license on Zenodo record 1245941
2. **Contact Guqin author**: Ask Wu Yusong about licensing for redistribution
3. **Contact Anthology author**: Clarify license for derived MIDI/MusicXML data
4. **Contact MGD authors**: Clarify license for folk song metadata
5. **Confirm CCOM-HuQin**: Verify it is NOT part of CCMusic ecosystem (different institution — CCOM vs CCOM/CCMusic)
6. **Check ACE-OpenCpop**: Confirm whether ACE extension carries Opencpop's application requirement
