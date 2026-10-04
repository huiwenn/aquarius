#!/bin/bash
# Family "image": sequential run queue that reproduces the reported numbers (shared, oversubscribed machine: one
# heavy job at a time, 2 threads each). Every step skips work already cached / already logged in results.csv.
# Run: bash src/regionclf/exp_image_queue.sh > data/regionclf/img/queue.log 2>&1
cd "$(dirname "$0")/../.."
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 VECLIB_MAXIMUM_THREADS=2 OPENBLAS_NUM_THREADS=2 PYTHONNOUSERSITE=1
PY="$HOME/miniforge3/envs/regionimg/bin/python -u"
$PY src/regionclf/exp_image_render.py --preview                              # 5 renderings (cached) + figure
$PY src/regionclf/exp_image_mfdmap.py                                        # MFDMap: E5prior replication + tasks
$PY src/regionclf/exp_image_embed.py --sources trans_primary,essen           # 3 backbones x 5 renderings
$PY src/regionclf/exp_image_frozen.py --tasks T15,T5,E,E5prior
$PY src/regionclf/exp_image_cnn.py --tasks T5 --renderings jianpu,roll,itrans,contour
$PY src/regionclf/exp_image_cnn.py --tasks T15,E5prior --renderings itrans,jianpu,roll
$PY src/regionclf/exp_image_cnn.py --tasks A5,E --renderings itrans,jianpu
$PY src/regionclf/exp_image_cnn.py --ensemble --tasks A5,E,T5,T15,E5prior --renderings itrans,jianpu
$PY src/regionclf/exp_image_cnn.py --ensemble --tasks T5,T15,E5prior --renderings itrans,jianpu,roll
$PY src/regionclf/exp_image_embed.py --backbones dinov2,clip --sources anthology   # resnet50 skipped for A5 (weakest)
$PY src/regionclf/exp_image_frozen.py --tasks A5
$PY src/regionclf/exp_image_mfdmap.py --diag
$PY src/regionclf/exp_image_cnn.py --tasks T5,E5prior --finetune itrans
$PY src/regionclf/exp_image_cnn.py --tasks T5,E5prior --finetune roll
$PY src/regionclf/exp_image_explain.py --tasks A5,E5prior,T5,T15
