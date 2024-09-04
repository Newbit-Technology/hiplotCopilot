import os
import pika
import json
from common.print_color import print_green, print_red


class RabbitMQClient:
    def __init__(self, username, password, host='127.0.0.1', queue_name='common'):
        self.rabbitmq_credentials = pika.PlainCredentials(username=username, password=password)
        self.rabbitmq_parameters = pika.ConnectionParameters(host=host, credentials=self.rabbitmq_credentials)
        self.connection = None
        self.channel = None
        self.queue_name = queue_name

        self.initialize_connection()

    def initialize_connection(self):
        """初始化连接和频道"""
        self.connection = pika.BlockingConnection(self.rabbitmq_parameters)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue_name, durable=True)

    def send_task(self,task_id , module_name: str, plugin_name: str, file_nums=1):
        """发送任务到指定队列"""
        # 设置任务文件的根目录
        prefix = os.path.abspath("../user/")

        # 构造任务的输入和输出文件前缀路径
        input_prefix = f"{prefix}/input/{task_id}"
        output_prefix = f"{prefix}/output/{task_id}"

        # 创建任务的输出目录，确保输出文件有地方存储
        os.makedirs(output_prefix, exist_ok=True)
        inputFile = ""
        for i in range(file_nums):
            if i == 0:
                inputFile = f"{input_prefix}/data.txt"
            else:
                inputFile += f",{input_prefix}/data{i}.txt"

        # 构造要发送的任务消息
        message = {
            "inputFile": f"{inputFile}",
            "confFile": f"{input_prefix}/data.json",
            "outputFilePrefix": output_prefix,
            "module": module_name,
            "tool": plugin_name,
            "ID": task_id,
            "Name": "common"
        }

        # 将任务消息转换为JSON格式的字符串
        message_json = json.dumps(message)

        # 发送消息到队列中
        try:
            self.channel.basic_publish(exchange="", routing_key=self.queue_name, body=message_json.encode(encoding="utf-8"))
        except:
            print_red(f"任务{task_id}提交失败")
            self.close_connection()
            self.initialize_connection()

        # 打印任务提交成功的消息
        print_green(f"任务{task_id}已提交")

    def close_connection(self):
        """关闭连接"""
        if self.connection and self.connection.is_open:
            self.connection.close()