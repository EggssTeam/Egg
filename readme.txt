conda remove -n summer1 --all -y
conda create -n summer1 python=3.10 -y
conda activate summer1
pip install -r requirements.txt
huggingface-cli download deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B
mongod
mongosh

uvicorn main:app --reloadREADME.md