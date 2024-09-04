from pymilvus import FieldSchema, DataType, CollectionSchema, Collection, list_collections

from common.print_color import print_green, print_yellow


def build_hiplot_plugins_text() -> Collection:
    print_green("Building hiplot_plugins collection and index......")

    # create collection
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=32, is_primary=True),
        FieldSchema(name="module", dtype=DataType.VARCHAR, max_length=32),
        FieldSchema(name="name", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=8192),
        FieldSchema(name="text_embeddings", dtype=DataType.FLOAT_VECTOR, dim=768)
    ]
    schema = CollectionSchema(fields, "Hiplot plugins text")
    # 获取所有集合
    collections = list_collections()

    # 检查目标集合是否存在
    target_collection = "hiplot_plugins_text"
    if target_collection in collections:
        hiplot_plugins_collection = Collection("hiplot_plugins_text")
        #if schema != hiplot_plugins_collection.schema:
            # 删除已存在的集合
        def drop_exit():
            nonlocal hiplot_plugins_collection
            hiplot_plugins_collection.drop()
            hiplot_plugins_collection = Collection("hiplot_plugins_text", schema)
            print("Dropped existing collection with mismatched schema.")

        # drop_exit() if input("是否删除已有集合? Y/n") == "Y" else print("Pass")
    else:
        hiplot_plugins_collection = Collection("hiplot_plugins_text", schema)

    index_params = {
        "index_type": "IVF_FLAT",
        "metric_type": "L2",
        "params": {"nlist": 128}
    }
    hiplot_plugins_collection.create_index("text_embeddings", index_params)
    print_green("Collection and index build successful!")
    hiplot_plugins_collection.load()
    return hiplot_plugins_collection

def build_hiplot_plugins_image() -> Collection:
    print_green("Building hiplot_plugins collection and index......")

    # create collection
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=32, is_primary=True),
        FieldSchema(name="module", dtype=DataType.VARCHAR, max_length=32),
        FieldSchema(name="name", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=8192),
        FieldSchema(name="image_embeddings", dtype=DataType.FLOAT_VECTOR, dim=768),
    ]
    schema = CollectionSchema(fields, "Hiplot plugins")
    # 获取所有集合
    collections = list_collections()

    # 检查目标集合是否存在
    target_collection = "hiplot_plugins_image"
    if target_collection in collections:
        hiplot_plugins_collection = Collection("hiplot_plugins_image")
        #if schema != hiplot_plugins_collection.schema:
        # 删除已存在的集合
        def drop_exit():
            nonlocal hiplot_plugins_collection
            hiplot_plugins_collection.drop()
            hiplot_plugins_collection = Collection("hiplot_plugins_image", schema)
            print("Dropped existing collection with mismatched schema.")
        # drop_exit() if input("是否删除已有集合? Y/n") == "Y" else print("Pass")
    else:
        hiplot_plugins_collection = Collection("hiplot_plugins_image", schema)

    index_params = {
        "index_type": "IVF_FLAT",
        "metric_type": "L2",
        "params": {"nlist": 128}
    }
    hiplot_plugins_collection.create_index("image_embeddings", index_params)
    print_green("Collection and index build successful!")
    hiplot_plugins_collection.load()
    return hiplot_plugins_collection


class CustomCollection():
    def __init__(self, text_collection:Collection, img_collection:Collection):
        self.text_collection = text_collection
        self.img_collection = img_collection

    def combined_search(self, text_embeddings, image_embeddings,  top_k=5, lambda_value=2):
        """
        结合文本嵌入和图像嵌入进行复合搜索。

        参数:
        - text_embeddings: 文本嵌入向量列表
        - image_embeddings: 图像嵌入向量列表
        - output_fields: 需要返回的字段列表
        - limit: 限制返回的结果数量，默认为5
        - lambda_value: 调整文本距离和图像距离组合得分的权重因子，默认为2

        返回:
        - combined_scores: 一个包含实体ID和组合得分的排序列表
        """
        print(text_embeddings.shape)
        print(image_embeddings.shape)
        # 搜索文本嵌入
        text_results = self.text_collection.search(
            data=[text_embeddings],
            anns_field="text_embeddings",
            param={"metric_type": "L2", "params": {"nprobe": 10}},
            limit=10,
            expr=None,
            output_fields=["id", "module", "name", "description"]
        )

        # 搜索图像嵌入
        image_results = self.img_collection.search(
            data=[image_embeddings],
            anns_field="image_embeddings",
            param={"metric_type": "L2", "params": {"nprobe": 10}},
            limit=10,
            expr=None,
            output_fields=["id", "module", "name", "description"]
        )

        # 计算 combined_scores
        combined_scores = {}
        # 使用字典记录文本结果
        img_dict = {hit.id: hit for hit in image_results[0]}

        for text_result in text_results:
            for text_hit in text_result:
                # 对每个图像结果，检查是否在文本结果中
                if text_hit.id in img_dict:
                    img_hit = img_dict[text_hit.id]
                    combined_score = text_hit.distance + lambda_value * img_hit.distance
                    combined_scores[text_hit.id] = {
                        "combined_score": combined_score,
                        "module": text_hit.module,  # 从文本结果获取 module
                        "name": text_hit.name,        # 从文本结果获取 name
                        "description": text_hit.description  # 从文本结果获取 description
                    }
                else:
                    combined_score = text_hit.distance
                    combined_scores[text_hit.id] = {
                        "combined_score": combined_score,
                        "module": text_hit.module,  # 从文本结果获取 module
                        "name": text_hit.name,        # 从文本结果获取 name
                        "description": text_hit.description  # 从文本结果获取 description
                    }

        # 排序并返回结果
        sorted_results = sorted(combined_scores.items(), key=lambda x: x[1]["combined_score"])

        return [{"id":id, "combined_score":info["combined_score"], "module":info["module"], "name":info["name"], "description":info["description"]} for id, info in sorted_results[:top_k]]