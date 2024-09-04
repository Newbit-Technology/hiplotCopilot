#%%
from transformers import AutoModel
import os
os.environ['https_proxy'] = 'http://127.0.0.1:1080'
# Initialize the model
model = AutoModel.from_pretrained('jinaai/jina-clip-v1', trust_remote_code=True)

# New meaningful sentences
sentences = ['A blue cat', 'A red cat, White background']

# Public image URLs
image_urls = [
    'https://hiplot.cn/img/cover/basic_area.jpg',
    'https://i.pinimg.com/736x/c9/f2/3e/c9f23e212529f13f19bad5602d84b78b.jpg'
]

# Encode text and images
text_embeddings = model.encode_text(sentences)
image_embeddings = model.encode_image(image_urls)  # also accepts PIL.image, local filenames, dataURI
print(text_embeddings[0].shape)
# Compute similarities
print(text_embeddings[0] @ text_embeddings[1].T) # text embedding similarity
print(text_embeddings[0] @ image_embeddings[0].T) # text-image cross-modal similarity
print(text_embeddings[0] @ image_embeddings[1].T) # text-image cross-modal similarity
print(text_embeddings[1] @ image_embeddings[0].T) # text-image cross-modal similarity
print(text_embeddings[1] @ image_embeddings[1].T)# text-image cross-modal similarity
#%%
from playwright.sync_api import sync_playwright

def get_image_urls(url):
    with sync_playwright() as p:
        # 启动无头浏览器
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 请求网页
        page.goto(url)

        # 获取指定元素下所有的 <img> 标签的 URL
        image_urls = page.query_selector_all('#main-content-card > form > div > div:nth-child(1) > div > div img')
        urls = [img.get_attribute('src') for img in image_urls]

        # 关闭浏览器
        browser.close()

        return urls

# 使用示例
url = 'https://hiplot.cn/basic/chord'  # 替换为你要请求的网页
image_urls = get_image_urls(url)
print(image_urls)

#%%
import requests
import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM



device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

model = AutoModelForCausalLM.from_pretrained("microsoft/Florence-2-large-ft", torch_dtype=torch_dtype, trust_remote_code=True).to(device)
processor = AutoProcessor.from_pretrained("microsoft/Florence-2-large-ft", trust_remote_code=True)

prompt = "<OD>"

url = "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/transformers/tasks/car.jpg?download=true"
image = Image.open(requests.get(url, stream=True).raw)

inputs = processor(text=prompt, images=image, return_tensors="pt").to(device, torch_dtype)

generated_ids = model.generate(
    input_ids=inputs["input_ids"],
    pixel_values=inputs["pixel_values"],
    max_new_tokens=1024,
    do_sample=False,
    num_beams=3
)
generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]

parsed_answer = processor.post_process_generation(generated_text, task="<OD>", image_size=(image.width, image.height))

print(parsed_answer)
#%%
from common.hiMilvus import hiplot_plugins_img
resp = hiplot_plugins_img.query(f"name==\"upset-plot\"", ["module"])
print(resp)