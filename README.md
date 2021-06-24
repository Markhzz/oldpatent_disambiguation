# Running clustering on KLC

## 1. 

```
module load python-anaconda3
conda create -n patent python==3.9
# conda install pytorch==1.2.0 torchvision==0.4.0 cudatoolkit=9.2 -c pytorch
source activate patent
pip install git+https://github.com/iesl/grinch.git --user
pip install -r /kellogg/data/patents/code/assignee_clustering/requirements.txt --user
conda install -c conda-forge wandb
pip install torch --user

# build the mentions
cd /kellogg/data/patents/code/assignee_clustering_stcy/
export PYTHONPATH=$PYTHONPATH:/kellogg/data/patents/code/assignee_clustering_stcy
python -m pv.disambiguation.assignee.build_assignee_klc_stcy

# run the clustering
wandb sweep bin/assignee/run_all_klc.yaml
wandb agent markhe/assignee_disambiguation/z9xsixiw

# finalize
python -m pv.disambiguation.assignee.finalize_klc_stcy

# extract a random sample to examine
python
import pandas as pd
full= pd.read_csv('/kellogg/data/patents/output/disambiguation_output.csv')
sample = full[:100000]
sample.to_csv('/kellogg/data/patents/output/disambiguation_output_sample.csv')

# 2nd stage build the mentions
python -m pv.disambiguation.assignee.build_assignee_klc_stcy_2stage

# 2nd stage run the clustering
wandb sweep bin/assignee/run_all_klc_2stage.yaml
wandb agent markhe/assignee_disambiguation/z9xsixiw

# 2nd stage finalize
python -m pv.disambiguation.assignee.finalize_klc_stcy_2stage

python
import pandas as pd
full= pd.read_csv('/kellogg/data/patents/output/disambiguation_output_2stage.csv')
sample = full[:100000]
sample.to_csv('/kellogg/data/patents/output/disambiguation_output_2stage_sample.csv')

```



