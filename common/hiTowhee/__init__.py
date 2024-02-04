from towhee import AutoPipes,AutoConfig

from common.print_color import print_green
import os
# get the built-in sentence_similarity pipeline
os.environ["https_proxy"] = "http://127.0.0.1:1080"
print_green("Loading embedding model......")
config = AutoConfig.load_config('sentence_embedding')
config.model = 'paraphrase-multilingual-mpnet-base-v2'
config.device = 0
embedding_pipeline = AutoPipes.pipeline('sentence_embedding', config=config)
print_green("Loading embedding model successful!")
del os.environ["https_proxy"]
