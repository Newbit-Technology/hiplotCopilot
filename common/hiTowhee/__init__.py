from transformers import AutoModel
import torch
import os
os.environ['https_proxy'] = 'http://127.0.0.1:1080'
# 检查 CUDA 是否可用
cuda_available = torch.cuda.is_available()

# 输出结果
if cuda_available:
    print("CUDA 可用，可以使用 GPU。")
model = AutoModel.from_pretrained('jinaai/jina-clip-v1', trust_remote_code=True,device_map="cuda")
del os.environ["https_proxy"]
