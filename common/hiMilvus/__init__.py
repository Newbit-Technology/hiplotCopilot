from pymilvus import connections
from common.print_color import print_green, print_red
from common.hiMilvus.hiplot_doc import build_hiplot_doc
from common.hiMilvus.hiplot_plugins import build_hiplot_plugins

try:
    print_green("Connecting milvus......")
    connections.connect(alias="default", host="127.0.0.1", port="19530")
    print_green("Milvus connect successful!")
except Exception as e:
    print_red(f"Failed to connect to Milvus: {e}")
    raise

# build
try:
    hiplot_doc_collection = build_hiplot_doc()
    hiplot_plugins_collection = build_hiplot_plugins()
except Exception as e:
    print_red(f"Failed to build collections: {e}")
    raise