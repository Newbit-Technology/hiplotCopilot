from transformers import AutoModel
import os
os.environ['https_proxy'] = 'http://127.0.0.1:1080'
# Initialize the model
model = AutoModel.from_pretrained('jinaai/jina-clip-v1', trust_remote_code=True)

# New meaningful sentences
sentences = ['A blue cat', 'A red cat, White background']

# Public image URLs
image_urls = [
    'https://i.pinimg.com/600x315/21/48/7e/21487e8e0970dd366dafaed6ab25d8d8.jpg',
    'https://i.pinimg.com/736x/c9/f2/3e/c9f23e212529f13f19bad5602d84b78b.jpg'
]

# Encode text and images
text_embeddings = model.encode_text(sentences)
image_embeddings = model.encode_image(image_urls)  # also accepts PIL.image, local filenames, dataURI