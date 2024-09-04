import json


class InputData:
    def __init__(self, title: list, data: list):
        self.title = title
        self.data = data

    def json_format(self) -> str:
        return json.dumps(self.__dict__)


def get_data_top(path: str, line_num: int = 3):
    """
    从指定文件路径读取前`line_num`行数据。

    首先读取文件标题作为数据标题，然后读取剩余各行数据。
    数据存储在一个自定义的`InputData`对象中，最后返回该对象的JSON格式表示。

    :param path: 文件路径
    :param line_num: 需要读取的行数，默认为6
    :return: 数据的JSON格式字符串
    """
    # 打开文件，准备读取数据
    with open(path, "r") as file:
        # 初始化InputData对象，用于存储读取的数据
        input_data = InputData([], [])

        # 循环读取指定行数的数据
        for i in range(line_num):
            # 读取文件下一行，并以空格分割为列表
            line = file.readline().split()

            # 如果是第一行，则认为是标题行，直接存储在InputData对象中
            if i == 0:
                input_data.title = line
                # 跳过当前循环，继续读取下一行
                continue

            # 将非标题行的数据追加到InputData对象的数据列表中
            input_data.data.append(line)

    # 返回读取数据的JSON格式字符串
    return input_data.json_format()

