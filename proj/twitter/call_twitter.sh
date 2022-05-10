#!/bin/bash

eval "$(conda shell.bash hook)"
conda activate kontinental
/Users/waynetailee/miniconda3/envs/kontinental/bin/python twitter_ingest.py
conda deactivate
