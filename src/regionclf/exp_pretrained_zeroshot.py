"""
Leakage / prior-knowledge probe: CLaMP 3 (C2) zero-shot region classification. The C2 checkpoint aligns the
symbolic encoder with an XLM-R text encoder on music–metadata pairs, so if its pretraining contained e.g. the Essen
China ABC files with their "O:"/region headers, text prompts naming the province should retrieve those songs
far above chance, while on the (post-2025, OCR'd) anthology they should not.

Prompt per class = mean of normalized text embeddings of
  "Chinese folk song from {province}" for every province mapped to the class (+ minority-group prompts) and
  "{色彩区}民歌". Prediction = argmax cosine(symbolic c2 embedding, class prompt). Scores are z-scored per class over items
(label-free calibration; raw argmax collapses onto one hub prompt). No training, no folds.
Logged as experiment "c2_zeroshot_{fmt}_{norm}".

Run (arm64 env; downloads FacebookAI/xlm-roberta-base config/tokenizer, weights come from the C2 checkpoint):
  PYTHONPATH=src ~/miniforge3/envs/regionclf/bin/python src/regionclf/exp_pretrained_zeroshot.py --emb mtf_raw
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf.common import labels, log_result, task  # noqa: E402
from regionclf.emb_clamp import W_C2  # noqa: E402
from regionclf.exp_pretrained import SOURCE, features  # noqa: E402
from secaiqu.mapping import PROVINCE_TO_SECAIQU  # noqa: E402

EXTRA = {"北方草原文化民歌区": ["Mongolian folk song", "Chinese folk song from Inner Mongolia"],
         "新疆民歌区": ["Uyghur folk song", "Chinese folk song from Xinjiang"],
         "藏族民歌区": ["Tibetan folk song", "Chinese folk song from Tibet"],
         "西南多民族古老原始文化民歌区": ["Miao folk song", "Dong folk song", "Yi folk song",
                                   "Chinese minority folk song from Guizhou"],
         "客家特区": ["Hakka folk song", "Hakka mountain song from Meizhou, Guangdong"]}


@torch.no_grad()
def text_encoder():
    from transformers import AutoConfig, AutoTokenizer, XLMRobertaModel
    name = "FacebookAI/xlm-roberta-base"
    tok = AutoTokenizer.from_pretrained(name)
    m = XLMRobertaModel(AutoConfig.from_pretrained(name), add_pooling_layer=True)
    sd = torch.load(W_C2, map_location="cpu", weights_only=True)["model"]
    miss = m.load_state_dict({k[len("text_model."):]: v for k, v in sd.items() if k.startswith("text_model.")},
                             strict=False)
    print("text_model load:", miss)
    proj = torch.nn.Linear(768, 768)
    proj.load_state_dict({k[len("text_proj."):]: v for k, v in sd.items() if k.startswith("text_proj.")})
    m.eval()

    def enc(texts):
        b = tok(texts, return_tensors="pt", padding=True, truncation=True, max_length=128)
        h = m(**b).last_hidden_state
        mask = b["attention_mask"].unsqueeze(-1).float()
        return proj((h * mask).sum(1) / mask.sum(1)).detach().numpy()
    return enc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emb", default="mtf_raw")
    ap.add_argument("--tasks", default="A5,E,T15,T5")
    a = ap.parse_args()
    enc = text_encoder()
    prov = defaultdict(list)
    for p, r in PROVINCE_TO_SECAIQU.items():
        if r:
            prov[r].append(p)
    for t in a.tasks.split(","):
        recs = task(t)
        y = labels(recs)
        classes = sorted(set(y))
        P = []
        for c in classes:
            prompts = [f"Chinese folk song from {p}" for p in prov.get(c, [])] + EXTRA.get(c, []) + [f"{c}民歌"]
            e = enc(prompts)
            e /= np.linalg.norm(e, axis=1, keepdims=True)
            P.append(e.mean(0))
        P = np.stack(P)
        P /= np.linalg.norm(P, axis=1, keepdims=True)
        X = features(recs, f"c2_{a.emb}", SOURCE[t])
        X /= np.linalg.norm(X, axis=1, keepdims=True)
        S = X @ P.T
        S = (S - S.mean(0)) / S.std(0)  # label-free calibration: raw argmax collapses onto one "hub" prompt
        pred = np.array(classes)[S.argmax(1)]
        log_result(f"c2_zeroshot_{a.emb}", "pretrained", t, y, pred,
                   notes="CLaMP3 C2 text-prompt zero-shot (no training; per-class score z-scored over items); "
                         "leakage/prior-knowledge probe")


if __name__ == "__main__":
    main()
