import string
from cgi import print_form

import nanoid
import os
import json
import shutil
from common.hiTowhee import embedding_pipeline
from common.print_color import print_blue
from common.hiMilvus import hiplot_plugins_collection
from langchain import LLMChain
from llm.chatOpenAI import chat_openai
from plugin_copilot.rabbitmq import send_task
from plugin_copilot.prompt import extract_params
from plugin_copilot.ui_json import get_table_required

class Task:
    project_path = os.path.abspath("../hiplot-org-plugins")
    destination_path = os.path.abspath("../user/input")
    print_blue(f"project_path\t{project_path}")

    def __init__(self, query: str):
        self.query = query
        self.tid = nanoid.generate(alphabet=string.digits + string.ascii_letters, size=10)
        self.image_description = ""
        self.data_filepath = ""
        self.title_description = ""
        self.module_name = ""
        self.plugin_name = ""
        self.plugin_path = ""
        self.hit_params_dict = {}
        self.input_json_required = ""
        self.json_llm = chat_openai().bind(response_format={"type": "json_object"})

    def run(self):
        print_blue(f"用户输入:{self.query}")

        # 1. 提取出需要绘制的图像和参数路径
        self.extract_params_from_query()

        # 2.确定所属模块和插件名
        self.get_module_and_plugin_name()

        # 3.解析data.txt文件
        # 3.1读取并解释标题信息
        self.get_title_description()
        # 3.2解析得到必填参数项
        self.get_input_json_required()
        # 3.3选择合适的参数填充
        self.get_hit_params()

        # 4.构造新的data.json
        self.build_new_json()

        # 5.将文件迁移到指定位置
        self.move_file()

        # 6.将构造好的所有内容提交至rscheduler运行
        self.send()

    def send(self):
        send_task(task_id=self.tid, module_name=self.module_name, plugin_name=self.plugin_name)

    def get_module_and_plugin_name(self):
        # 根据图像描述和预训练的模型来确定插件名，并获取相应的模块名
        # 获取插件名
        from plugin_copilot.prompt import get_plugin_name
        # 使用图像描述生成embeddings，并进一步获取相关文档
        embeddings = embedding_description(self.image_description)
        documents = get_description(embeddings)
        # 使用LLMChain和get_plugin_name提示模板来运行，以确定插件名
        c = LLMChain(llm=chat_openai().bind(response_format={"type": "json_object"}), prompt=get_plugin_name)
        resp = c.run(image_description=self.image_description, documents=documents)
        hit_description = json.loads(resp)
        # 查询插件所属的模块
        for name, _ in hit_description.items():
            self.plugin_name = name
            # 根据插件名查询其所属模块
            resp = hiplot_plugins_collection.query(f"name==\"{name}\"", ["module"])
            if len(resp) == 0:
                print("Record not found")
            self.module_name = resp[0]["module"]
            break
        # 打印插件所属模块和插件名
        print_blue(f"所属模块:{self.module_name}")
        print_blue(f"插件名:{self.plugin_name}")
        # 获取插件路径
        self.get_plugin_path()

    def extract_params_from_query(self):
        """
        从查询请求中提取参数。

        使用plugin_copilot.prompt中的extract_params工具，通过LLMChain从查询(self.query)中提取参数，
        并将这些参数用于后续的图像描述和数据文件路径的获取。
        """
        # 导入extract_params工具，用于提取查询参数
        print(self.query)
        resp = self.json_llm.invoke(extract_params.format(sentence=self.query))
        print(resp.content)

        # 将响应内容从JSON格式解析为字典，以便提取所需参数
        params = json.loads(resp.content)

        # 提取图像描述参数，并使用print_blue函数打印出图像描述信息
        i_description = params["image_description"]
        print_blue(f"图像描述信息:{i_description}")

        # 提取数据文件路径参数，并使用os.path.abspath确保路径的准确性，然后使用print_blue函数打印出数据文件路径
        d_filepath = os.path.abspath(params["filepath"])
        print_blue(f"数据文件路径:{d_filepath}")

        # 将提取的图像描述和数据文件路径保存到实例变量中，以便后续使用
        self.image_description = i_description
        self.data_filepath = d_filepath

    def get_title_description(self):
        from plugin_copilot.prompt import explain_title
        from plugin_copilot.data_txt import get_data_top
        resp = self.json_llm.invoke(explain_title.format(json_data=get_data_top(self.data_filepath)))
        t_description = resp.content
        print_blue(f"标题解释:{t_description}")
        self.title_description = t_description

    def get_input_json_required(self):
        ui_json_file_path = os.path.join(self.plugin_path, "ui.json")
        with open(ui_json_file_path, "r", encoding="utf-8") as f:
            ui = json.load(f)
        table_required = get_table_required(ui)
        self.input_json_required = json.dumps(table_required)
        print_blue(f"必填参数解析结果:{self.input_json_required}")

    def move_file(self):
        input_path = os.path.join(self.destination_path, self.tid)
        os.makedirs(input_path, exist_ok=True)
        new_data_path = shutil.copy(os.path.abspath("../data.txt"), os.path.join(input_path, "data.txt"))
        new_config_path = shutil.copy(os.path.abspath("../data.json"), os.path.join(input_path, "data.json"))
        # os.remove("../data.txt")
        # os.remove("../data.json")
        print_blue(f"用户提交的data.txt已迁移至{new_data_path}")
        print_blue(f"新构造的data.json已移动至{new_config_path}")

    def get_hit_params(self):
        from plugin_copilot.prompt import select_params
        resp = self.json_llm.invoke(select_params.format(description_json=self.title_description, input_json=self.input_json_required))
        h_params = resp.content
        self.hit_params_dict = json.loads(h_params)

    def build_new_json(self):
        with open(os.path.join(self.plugin_path, "data.json"), "r", encoding="utf-8") as f:
            data_json = json.load(f)
        for k, v in self.hit_params_dict.items():
            table_num, data_num = map(int, k.split("-"))
            key = f"{table_num}-data"
            data_json["params"]["config"]["dataArg"][key][data_num - 1]["value"] = v
        with open("../data.json", "w") as f:
            json.dump(data_json, f, indent=2)

    def get_plugin_path(self):
        self.plugin_path = os.path.join(self.project_path, self.module_name, self.plugin_name)


def embedding_description(desc: str):
    return embedding_pipeline(desc).get()


def get_description(embedding) -> str:
    """
    根据嵌入数据检索并返回描述信息。

    该函数通过搜索嵌入数据来获取相关描述。它定义了搜索参数，执行搜索，然后解析结果，
    最后以JSON字符串格式返回所需的描述信息。

    参数:
    embedding: 嵌入数据，用于在hiplot_plugins_collection中搜索。

    返回:
    str: 包含搜索结果中每个条目名称和描述的JSON字符串。
    """
    # 定义搜索参数，包括匹配度量类型和搜索结果的起始位置
    search_params = {"metric_type": "L2", "offset": 0}

    # 在指定的集合中根据嵌入数据和参数进行搜索，限制返回结果数量，并指定要输出的字段
    result = hiplot_plugins_collection.search(
        data=embedding,
        anns_field="embeddings",
        param=search_params,
        limit=5,
        output_fields=["description", "name"]
    )

    # 初始化一个字典来存储搜索结果的描述信息
    docs = {}
    for hits in result:
        for hit in hits:
            # 获取并解析每个搜索结果的描述信息
            description = hit.entity.get("description")
            description_decode = json.loads(description)

            # 获取搜索结果的名称，并将其与解析后的描述信息一起存入字典
            hit_name = hit.entity.get("name")
            docs[hit_name] = description_decode

    # 将收集到的描述信息转换为JSON字符串格式并返回
    return json.dumps(docs, ensure_ascii=False)


if __name__ == "__main__":
    query = "帮我给../data.txt文件画一幅区间区域图"
    t = Task(query)
    t.run()
