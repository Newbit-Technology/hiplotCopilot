class TableArg:
    en_description: str = (
        "This field represents {} and requires selecting the appropriate field from the data table as its value"
    )
    zh_description: str = "这个字段表示{}，需要从数据表中选择合适的字段作为其值"

    def __init__(self, arg: dict):
        self.arg = arg

    def get_prompt(self) -> str:
        label = self.arg["label"]
        if "en" in label:
            return self.en_description.format(label["en"])
        elif "zh_cn" in label:
            return self.zh_description.format(label["zh_cn"])
        return "language type not found"

    def is_required(self) -> bool:
        return "required" in self.arg and self.arg["required"]


class ExtraArg:

    def __init__(self, name: str, data: dict, data_json: dict):
        self.name = name
        self.data = data
        self.data_json = data_json["params"]["config"]["extra"]

    def get_prompt(self) -> str:
        label = self.data["label"]
        items = ""
        range = ""
        if "en" in label:
            description = f"This field represents {label["en"]}.The default value is {self.data_json[self.name]}."
        else:
            description = f"The type of this field is {label}.The default value is {self.data_json[self.name]}."

        if "items" in self.data:
            items = f"The options for this parameter are as follows.{self.data["items"]}"

        if "min" in self.data or "max" in self.data:
            range = "The value range of this parameter is {}".format(
                self.data["min"] if "min" in self.data else "-inf"
            ) + " to {}".format(self.data["max"] if "max" in self.data else "inf")

        return f"{description}\n{items}\n{range}\n"


def get_table_required(ui_json) -> dict:
    """
    从给定的UI JSON配置中提取所有必填项的数据和其余参数。

    参数:
    ui_json (dict): 包含UI配置的字典，其中包括数据参数(dataArg)。

    返回:
    dict: 一个字典，键为表格和字段的编号组合，值为字段的提示信息。
    """
    # 初始化一个空字典来存储必填项
    table_required = {}

    # 从 ui_json 中获取数据参数
    data_arg = ui_json.get("dataArg", {})
    for table_name, table_args in data_arg.items():
        for arg in table_args:
            # 创建 TableArg 对象
            table_arg = TableArg(arg)

            # 如果当前字段不是必填项，则跳过
            if not table_arg.is_required():
                continue

            # 将字段提示添加到 table_required 字典中
            table_required[table_name] = table_arg.get_prompt()

    # 返回必填项字典
    return table_required


def get_extra_required(ui_json, data_json) -> dict:
    """
    获取UI配置中必要的额外参数。

    本函数遍历UI配置文件中的"extra"项，筛选出必要的额外参数。
    必要的判断条件为：参数必须是必需的（is_required）且参数配置中明确标示为必需（"required"字段）。

    参数:
    - ui_json: 包含UI配置的JSON文件，其中含有"extra"字段。

    返回:
    - 一个字典，键为额外参数的名称，值为参数的提示信息。
    """
    # 提取UI配置文件中的"extra"部分
    extra = ui_json.get("extra", {})
    # 初始化一个空字典，用于存储必要的额外参数
    extra_required = {}

    # 遍历"extra"字典中的每一项
    for k, v in extra.items():
        # 创建ExtraArg实例，用于进一步处理当前项
        extra_arg = ExtraArg(k, v, data_json)
        # 如果当前项是必需的，将其提示信息添加到extra_required字典中
        extra_required[k] = extra_arg.get_prompt()

    # 返回存储了必要额外参数的字典
    return extra_required
