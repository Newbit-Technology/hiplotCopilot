class TableArg:
    en_description: str = "This field represents {} and requires selecting the appropriate field from the data table as its value"
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
    def __init__(self, name: str, data: dict):
        self.name = name
        self.data = data

    def get_prompt(self) -> str:
        return self.name

    def is_required(self) -> bool:
        # return "required" in self.data and self.data["required"]
        # TODO
        return False


def get_table_required(ui_json) -> dict:
    # 从 ui_json 中获取数据参数
    data_arg = ui_json["dataArg"]

    # 初始化当前表格计数器
    cur_table = 0

    # 初始化一个空字典来存储必填项
    table_required = {}

    # 循环处理每一个表格
    while True:
        # 增加表格计数器
        cur_table += 1

        # 构造当前表格的名字
        table_name = f"{cur_table}-data"

        # 如果当前表格的名字不在 data_arg 中，则退出循环
        if table_name not in data_arg:
            break

        # 初始化字段计数器
        arg_num = 0

        # 遍历当前表格中的每个字段
        for arg in data_arg[table_name]:
            # 增加字段计数器
            arg_num += 1

            # 创建 TableArg 对象
            table_arg = TableArg(arg)

            # 如果当前字段不是必填项，则跳过
            if not table_arg.is_required():
                continue

            # 构造键值
            key = f"{cur_table}-{arg_num}"

            # 将字段提示添加到 table_required 字典中
            table_required[key] = table_arg.get_prompt()

    # 返回必填项字典
    return table_required



def get_extra_required(ui_json) -> dict:
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
    extra = ui_json["extra"]
    # 初始化一个空字典，用于存储必要的额外参数
    extra_required = {}

    # 遍历"extra"字典中的每一项
    for k, v in extra.items():
        # 创建ExtraArg实例，用于进一步处理当前项
        extra_arg = ExtraArg(k, v)

        # 如果当前项不是必需的，则跳过
        if not extra_arg.is_required():
            continue

        # 如果当前项的配置中没有明确标示为必需，则跳过
        if "required" not in v or not v["required"]:
            continue

        # 如果当前项是必需的，将其提示信息添加到extra_required字典中
        extra_required[k] = extra_arg.get_prompt()

    # 返回存储了必要额外参数的字典
    return extra_required

