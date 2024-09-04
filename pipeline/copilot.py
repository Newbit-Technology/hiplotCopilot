import json
import os
import pprint
import shutil
import string
import subprocess

import nanoid
from langchain_core.messages import BaseMessage

from common.hiMilvus import custom_collection, hiplot_plugins_text
from common.hiTowhee import model
from common.print_color import print_blue, print_yellow
from llm.chatOpenAI import chat_openai, encode_image_message, chat_claude
from plugin_copilot.prompt import describe_image, explain_plug, select_extra_params
from plugin_copilot.rabbitmq import RabbitMQClient
from plugin_copilot.ui_json import get_table_required, get_extra_required


class DrawChart:
    project_path = os.path.abspath("../hiplot-org-plugins")
    destination_path = os.path.abspath("../user/input")
    print_blue(f"project_path\t{project_path}")

    def __init__(self, llm, vlm, json_llm, json_vlm, session_path, rabbitmq_client):
        self.input_extra_required = None
        self.data_top = None
        self.figures = None
        self.llm = llm
        self.vlm = vlm
        self.json_llm = json_llm
        self.json_vlm = json_vlm
        self.session_path = session_path
        self.session_path = session_path
        self.figures = None
        self.img_url = ""
        self.image_filepath = ""
        self.tid = nanoid.generate(alphabet=string.digits + string.ascii_letters, size=10)
        self.image_description = ""
        self.data_filepath = ""
        self.title_description = ""
        self.module_name = ""
        self.plugin_name = ""
        self.plugin_path = ""
        self.hit_params_dict = {}
        self.input_json_required = ""
        self.llm = llm
        self.json_llm = json_llm
        self.rabbitmq_client = rabbitmq_client

    def run(self, image_path, module_name, data_type, plugin_name):
        self.plugin_name = plugin_name
        self.module_name = module_name
        self.data_type = data_type
        self.get_input_arg_required()
        # 3.选择合适的参数填充
        self.get_title_description()
        self.get_hit_params(image_path)

        # 4.构造新的data.json
        self.build_new_json()

        # 5.将文件迁移到指定位置
        self.move_file()

        return self.send(module_name, plugin_name)

    def send(self, module_name, plugin_name):
        self.rabbitmq_client.send_task(self.tid, module_name=module_name, plugin_name=plugin_name)
        return f"任务{self.tid}已提交,module_name={module_name}, plugin_name={plugin_name}"

    def get_title_description(self):
        from plugin_copilot.prompt import explain_title
        from plugin_copilot.data_txt import get_data_top

        # 遍历所有data{i}.txt形式的文件
        self.title_descriptions = {}
        table_names = list(self.data["params"]["config"]["data"].keys())
        for i in range(0, 100):
            if i == 0:
                file_path = f"{self.session_path}/data.txt"
            else:
                file_path = f"{self.session_path}/data{i}.txt"

            if os.path.exists(file_path):
                resp = self.json_llm.invoke(explain_title.format(json_data=get_data_top(file_path)))
                t_description = resp.content
                print_blue(f"标题解释:{t_description}")
                self.title_descriptions[table_names[i]] = t_description
            else:
                break

        for i in range(1, 100):
            if i == 0:
                file_path = f"{self.session_path}/data.txt"
            else:
                file_path = f"{self.session_path}/data{i}.txt"

            if os.path.exists(file_path):
                self.data_top[table_names[i]] = get_data_top(file_path)
            else:
                break

    def get_input_arg_required(self):
        self.get_plugin_path()
        ui_json_file_path = os.path.join(self.plugin_path, f"ui.json")
        data_json_file_path = os.path.join(self.plugin_path, f"data.json")
        with open(ui_json_file_path, "r", encoding="utf-8") as f:
            ui = json.load(f)
        with open(data_json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        table_required = get_table_required(ui)
        extra_required = get_extra_required(ui, data)
        self.ui = ui
        self.data = data
        self.input_json_required = json.dumps(table_required)
        self.input_extra_required = json.dumps(extra_required)
        print_blue(f"必填参数解析结果:{self.input_json_required}")
        print_blue(f"额外参数解析结果:{self.input_extra_required}")

    def move_file(self):
        input_path = os.path.join(self.destination_path, self.tid)
        os.makedirs(input_path, exist_ok=True)
        # 遍历所有data{i}.txt形式的文件
        for i in range(0, 100):
            if i == 0:
                file_path = f"data.txt"
            else:
                file_path = f"data{i}.txt"
            if os.path.exists(file_path):
                shutil.copy(os.path.abspath(f"{self.session_path}/{file_path}"), os.path.join(input_path, file_path))
            else:
                break

        new_config_path = shutil.copy(
            os.path.abspath(f"{self.session_path}/data.json"), os.path.join(input_path, f"data.json")
        )
        print_blue(f"用户提交的data.txt已迁移至{input_path}")
        print_blue(f"新构造的data.json已移动至{new_config_path}")

    def get_hit_params(self, image_path):
        print(image_path)
        from plugin_copilot.prompt import select_params

        if self.input_json_required != {}:
            describe: BaseMessage = select_params.format(
                description_json=self.title_descriptions, input_json=self.input_json_required
            )
            resp = self.json_llm.invoke([encode_image_message(describe, image_path)])
            t_params = resp.content
            self.hit_params_dict = json.loads(t_params)

        if self.input_extra_required != {}:
            # 如果explain_plug.txt存在，则使用explain_plug.txt作为描述
            if os.path.exists(f"{self.session_path}/explain_plug.txt"):
                with open(f"{self.session_path}/explain_plug.txt", "r") as f:
                    pre_describe = f.read()
            describe = select_extra_params.format(
                description=f"{pre_describe}", item={self.input_extra_required}, data_type=self.data_type
            )
            resp = self.json_vlm.invoke([encode_image_message(describe, image_path)])
            e_params = resp.content
            self.hit_params_dict = json.loads(e_params)

        print("命中参数", self.input_json_required)
        print("命中额外参数", self.hit_params_dict)

    def build_new_json(self):
        with open(os.path.join(self.plugin_path, "data.json"), "r", encoding="utf-8") as f:
            data_json = json.load(f)

        data_num = 0
        if "dataArg" in data_json["params"]["config"]:
            for k, v in self.hit_params_dict.items():
                data_json["params"]["config"]["dataArg"][k][data_num]["value"] = v
                data_num += 1

        if "extra" in data_json["params"]["config"]:
            for k, v in self.hit_params_dict.items():
                data_json["params"]["config"]["extra"][k] = v

        with open(f"{self.session_path}/data.json", "w") as f:
            json.dump(data_json, f, indent=2)

    def get_plugin_path(self):
        self.plugin_path = os.path.join(self.project_path, self.module_name, self.plugin_name)


class ChooseChart:
    project_path = os.path.abspath("../hiplot-org-plugins")
    destination_path = os.path.abspath("../user/input")
    print_blue(f"project_path\t{project_path}")

    def __init__(self, llm, vlm, json_llm, json_vlm, session_path, rabbitmq_client):
        self.figures = None
        self.llm = llm
        self.vlm = vlm
        self.json_llm = json_llm
        self.json_vlm = json_vlm
        self.session_path = session_path
        self.session_path = session_path
        self.figures = None
        self.img_url = ""
        self.image_filepath = ""
        self.tid = nanoid.generate(alphabet=string.digits + string.ascii_letters, size=10)
        self.image_description = ""
        self.data_filepath = ""
        self.title_description = ""
        self.module_name = ""
        self.plugin_name = ""
        self.plugin_path = ""
        self.hit_params_dict = {}
        self.input_json_required = ""
        self.llm = llm
        self.json_llm = json_llm
        self.rabbitmq_client = rabbitmq_client

    def run(self, renderURL):
        for filename in os.listdir(f"{self.session_path}"):
            if filename.startswith("figures") and filename.endswith(".json"):
                self.figures = json.load(open(filename))

        # 绘制用户选择的renderURL
        for figure in self.figures:
            if figure["renderURL"] == renderURL:
                caption = figure["caption"]
                image_path = figure["renderURL"]

                # 1.提取出需要绘制的图像和参数路径
                self.get_image_describe(caption, image_path)

                # 2.确定所属模块和插件名
                self.get_module_and_plugin_name()

                # 3.解释插件
                return self.explain_plug(self.plugin_path)
            else:
                return "请选择正确的图表"

    def read_chart(self):
        with open(f"{self.session_path}/figures.json", "r", encoding="utf-8") as f:
            self.figures = json.load(f)

    def explain_plug(self, plugin_path):
        ui_json_file_path = os.path.join(plugin_path, "ui.json")
        meta_json_file_path = os.path.join(plugin_path, "meta.json")
        data_file_path = os.path.join(plugin_path, "data.json")
        readme_file_path = os.path.join(plugin_path, "README.md")

        # 读取文件内容
        with open(ui_json_file_path, "r", encoding="utf-8") as f:
            ui_json = f.read()

        with open(meta_json_file_path, "r", encoding="utf-8") as f:
            meta_json = f.read()

        with open(data_file_path, "r", encoding="utf-8") as f:
            data_md = f.read()

        with open(readme_file_path, "r", encoding="utf-8") as f:
            readme_md = f.read()

        # 将文件内容插入到explain_plug里
        resp = self.llm.invoke(explain_plug.format(ui=ui_json, meta=meta_json, data=data_md, readme=readme_md)).content
        with open(f"{self.session_path}/explain_plug.txt", "w") as f:
            f.write(resp)
        respponse = f"""我们根据图像描述，插件名称为找到了一个插件
        插件的描述如下:
        {resp}
        插件的所属模块和插件名如下:
        所属模块:{self.module_name}
        插件名:{self.plugin_name}
        请严格根据插件名调用
        """
        return respponse

    def get_module_and_plugin_name(self):
        # 根据图像描述和预训练的模型来确定插件名，并获取相应的模块名
        # 获取插件名
        from plugin_copilot.prompt import get_plugin_name

        # 使用图像描述生成embeddings，并进一步获取相关文档
        text_embedding, img_embedding = self.embedding_description(self.image_description, self.image_filepath)
        documents = self.get_description(text_embedding, img_embedding)
        # 使用LLMChain和get_plugin_name提示模板来运行，以确定插件名
        print(documents)
        resp = self.json_llm.invoke(
            get_plugin_name.format(image_description=self.image_description, documents=documents)
        ).content
        print(resp)
        if resp != "None":
            hit_description: dict = json.loads(resp)

            print(list(hit_description.values())[0])
            name = list(hit_description.values())[0]["name"]
            # 查询插件所属的模块
            resp = hiplot_plugins_text.query(f'name=="{name}"', ["module"])
            self.module_name = resp[0]["module"]
            self.plugin_name = name
            # 打印插件所属模块和插件名
            print_blue(f"所属模块:{self.module_name}")
            print_blue(f"插件名:{self.plugin_name}")
            # 获取插件路径
            self.get_plugin_path()
        else:
            print("未找到对应插件")

    def get_image_describe(self, caption, image_path):

        describe: BaseMessage = describe_image.format(caption=caption)
        resp = self.llm.invoke([encode_image_message(describe, image_path)])
        self.image_description = resp.content
        self.image_filepath = image_path
        print_blue(f"图像描述信息:{self.image_description}")

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
        new_data_path = shutil.copy(
            os.path.abspath(f"{self.session_path}/data.txt"), os.path.join(input_path, "data.txt")
        )
        new_config_path = shutil.copy(
            os.path.abspath(f"{self.session_path}/data.json"), os.path.join(input_path, "data.json")
        )
        # os.remove("../data.txt")
        # os.remove("../data.json")
        print_blue(f"用户提交的data.txt已迁移至{new_data_path}")
        print_blue(f"新构造的data.json已移动至{new_config_path}")

    def get_hit_params(self):
        from plugin_copilot.prompt import select_params

        resp = self.json_llm.invoke(
            select_params.format(description_json=self.title_description, input_json=self.input_json_required)
        )
        h_params = resp.content
        self.hit_params_dict = json.loads(h_params)
        print(self.hit_params_dict)

    def build_new_json(self):
        with open(os.path.join(self.plugin_path, "data.json"), "r", encoding="utf-8") as f:
            data_json = json.load(f)
        for k, v in self.hit_params_dict.items():
            table_num, data_num = map(int, k.split("-"))
            key = f"{table_num}-data"
            data_json["params"]["config"]["dataArg"][key][data_num - 1]["value"] = v
        with open(f"{self.session_path}/data.json", "w") as f:
            json.dump(data_json, f, indent=2)

    def get_plugin_path(self):
        self.plugin_path = os.path.join(self.project_path, self.module_name, self.plugin_name)

    def embedding_description(self, desc: str, image_url: str):
        text_embedding = model.encode_text(desc)
        img_embedding = model.encode_image(image_url)
        return text_embedding, img_embedding

    def get_description(self, text_embedding, img_embedding) -> str:
        """
        根据嵌入数据检索并返回描述信息。

        该函数通过搜索嵌入数据来获取相关描述。它定义了搜索参数，执行搜索，然后解析结果，
        最后以JSON字符串格式返回所需的描述信息。

        参数:
        embedding: 嵌入数据，用于在hiplot_plugins_collection中搜索。

        返回:
        str: 包含搜索结果中每个条目名称和描述的JSON字符串。
        """
        # 在指定的集合中根据嵌入数据和参数进行搜索，限制返回结果数量，并指定要输出的字段
        result = custom_collection.combined_search(text_embeddings=text_embedding, image_embeddings=img_embedding)

        # 初始化一个字典来存储搜索结果的描述信息
        docs = {}
        for hits in result:
            docs[hits["id"]] = {"name": hits["name"], "module": hits["module"], "description": hits["description"]}

        # 将收集到的描述信息转换为JSON字符串格式并返回
        return json.dumps(docs, ensure_ascii=False)


class ReadChart:
    def __init__(self, llm, vlm, json_llm, json_vlm, session_path, rabbitmq_client):
        self.figures = None
        self.llm = llm
        self.vlm = vlm
        self.json_llm = json_llm
        self.json_vlm = json_vlm
        self.session_path = session_path
        self.rabbitmq_client = rabbitmq_client

    def run(self, path):
        self.extract_caption(path)
        return self.read_chart()

    def extract_caption(self, path):
        # 调用Java模块并运行命令
        process = subprocess.Popen(
            [
                "java",
                "-jar",
                "/home/lujunjie16/pdffigures2/pdffigures2.jar",
                path,
                "-g",
                f"{self.session_path}/temp.json",
                "-m",
                "temp",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate()

        # 等待进程完成
        while process.poll() is None:
            pass

        # 检查是否有错误
        if process.returncode != 0:
            print(f"Error: {stderr}")
        else:
            print(f"Output: {stdout}")

    def read_chart(self):
        # 读取目录下temp开头的json文件
        for filename in os.listdir(f"{self.session_path}"):
            if filename.startswith("temp") and filename.endswith(".json"):
                path = os.path.join(f"{self.session_path}", filename)
                with open(path, "r", encoding="utf-8") as f:
                    figures = json.load(f)["figures"]
        # 根据renderURL去重,保留每个url的第一个
        seen_urls = set()
        unique_figures = []

        for figure in figures:
            render_url = figure["renderURL"]
            if render_url not in seen_urls:
                unique_figures.append(figure)
                seen_urls.add(render_url)

        figures = []
        for unique_figure in unique_figures:
            figures.append({"caption": unique_figure["caption"], "renderURL": unique_figure["renderURL"]})
        response = f"""
        已读取{len(unique_figures)}个图表,内容如下:
        {pprint.pformat(figures)}
        """
        # 写入到figures.json
        with open(f"{self.session_path}/temp.json", "w") as f:
            json.dump(figures, f, indent=2)

        print_blue(response)
        return response


class FileTools:
    def __init__(self, llm, json_llm, session_path):
        self.llm = llm
        self.json_llm = json_llm
        self.session_path = session_path

    def get_file_list(self, path):
        file_list = []
        path = f"{os.path.join(self.session_path, path)}"
        print_yellow(path)
        for filename in os.listdir(path):
            file_list.append(filename)
        return file_list


class TalkHelper:
    def __init__(self):
        self.session_id = nanoid.generate(alphabet=string.digits + string.ascii_letters, size=10)
        self.talk_helper = None
        self.json_llm = chat_openai().bind(response_format={"type": "json_object"})
        self.json_vlm = chat_claude().bind(response_format={"type": "json_object"})
        self.llm = chat_openai()
        self.vlm = chat_claude()
        self.session_path = os.path.join("sessions", self.session_id)
        os.makedirs(self.session_path, exist_ok=True)
        self.rabbitmq_client = RabbitMQClient(username="lujunjie", password="q852853q")
        self.read_chart = ReadChart(
            self.vlm, self.llm, self.json_llm, self.json_vlm, self.session_path, self.rabbitmq_client
        )
        self.choose_chart = ChooseChart(
            self.vlm, self.llm, self.json_llm, self.json_vlm, self.session_path, self.rabbitmq_client
        )
        self.draw_chart = DrawChart(
            self.llm, self.llm, self.json_llm, self.json_vlm, self.session_path, self.rabbitmq_client
        )
        self.file_tools = FileTools(self.llm, self.llm, self.session_path)

        self.functions = [
            {
                "name": "read_chart",
                "description": "读取图表",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "输入您想要读取的图表的路径。 示例：/path/to/your/chart.pdf",
                        },
                    },
                    "required": ["path"],
                },
            },
            {
                "name": "get_file_list",
                "description": "读取当前环境下目录的文件列表",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "输入您想要读取的目录的路径。 示例：/path/to/your/dir",
                        },
                    },
                    "required": ["path"],
                },
            },
            {
                "name": "choose_chart",
                "description": "选择并解释一个图表插件",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "renderURL": {
                            "type": "string",
                            "description": "要选择的图表的渲染URL。示例：figures/example_chart.png",
                        },
                    },
                    "required": ["renderURL"],
                },
            },
            {
                "name": "draw_chart",
                "description": "绘制图表并处理相关数据",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_path": {"type": "string", "description": "输入图像文件的路径。例如：/path/to/image.jpg"},
                        "module_name": {"type": "string", "description": "要使用的模块名称。例如：basic"},
                        "plugin_name": {"type": "string", "description": "要使用的插件名称。例如：scatter"},
                        "data_type": {"type": "string", "description": "要填写的数据表格的类型，例如：list"},
                    },
                    "required": ["image_path", "module_name", "plugin_name", "data_type"],
                },
            },
        ]
        self.func_llm = self.llm.bind_tools(self.functions, tool_choice="auto")

    def func_call(self, function_name, arguments):
        resp = ""
        # 根据函数名称执行对应的函数
        match function_name:
            case "read_chart":
                resp = self.read_chart.run(arguments["path"])
            case "choose_chart":
                resp = self.choose_chart.run(arguments["renderURL"])
            case "draw_chart":
                resp = self.draw_chart.run(
                    arguments["image_path"],
                    arguments["module_name"],
                    arguments["data_type"],
                    arguments["plugin_name"],
                )
            case "get_file_list":
                resp = self.file_tools.get_file_list(arguments["path"])

        return resp
