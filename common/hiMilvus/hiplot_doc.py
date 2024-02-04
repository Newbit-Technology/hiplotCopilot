from pymilvus import FieldSchema, CollectionSchema, Collection, DataType

from common.print_color import print_green


def build_hiplot_doc() -> Collection:
    print_green("Building hiplot_doc collection and index......")

    # create collection
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=32, is_primary=True),
        FieldSchema(name="embeddings", dtype=DataType.FLOAT_VECTOR, dim=768),
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=8192)
    ]

    schema = CollectionSchema(fields, "Hiplot docs")
    hiplot_doc_collection = Collection("hiplot_doc")
    #if schema != hiplot_doc_collection.schema:
        # 删除已存在的集合
    def drop_exit():
        nonlocal hiplot_doc_collection
        hiplot_doc_collection.drop()
        hiplot_doc_collection = Collection("hiplot_doc", schema)
        print_green("New collection created.")
    drop_exit() if input("是否删除已有集合? Y/n") == "Y" else print("Retain Dropped existing collection")

    #else:
    #    print("Collection already exists with matching schema.")

    # create index
    index = {
        "index_type": "IVF_FLAT",
        "metric_type": "L2",
        "params": {"nlist": 128}
    }
    hiplot_doc_collection.create_index("embeddings", index)
    print_green("Collection and index build successful!")
    hiplot_doc_collection.load()
    return hiplot_doc_collection
