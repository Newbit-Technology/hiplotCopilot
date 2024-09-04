import os

import pika
import json

from common.print_color import print_green

# RabbitMQ 服务器的连接参数
rabbitmq_credentials = pika.PlainCredentials(username='lujunjie', password='q852853q')
rabbitmq_parameters = pika.ConnectionParameters(host='127.0.0.1', credentials=rabbitmq_credentials)
connection = pika.BlockingConnection(rabbitmq_parameters)
channel = connection.channel()
queue_name = 'common'


def send_task(task_id: str, module_name: str, plugin_name: str, file_nums=1):
    """
    发送任务到指定队列。

    本函数负责将任务信息打包成JSON消息，然后发送到一个预先声明的、持久化的队列中。
    该队列保证消息在传输中的可靠性，确保任务能够被后端处理模块消费和执行。

    参数:
    - task_id (str): 任务的唯一标识符。
    - module_name (str): 指定要执行的功能模块名。
    - plugin_name (str): 指定执行任务的插件名。

    返回:
    无返回值，但函数会在控制台打印任务提交成功的消息。
    """
    # 声明一个持久化的队列，确保队列在重启RabbitMQ后依然存在
    channel.queue_declare(queue=queue_name, durable=True)

    # 设置任务文件的根目录
    prefix = os.path.abspath("../user/")

    # 构造任务的输入和输出文件前缀路径
    input_prefix = f"{prefix}/input/{task_id}"
    output_prefix = f"{prefix}/output/{task_id}"

    # 创建任务的输出目录，确保输出文件有地方存储
    os.mkdir(output_prefix)
    inputFile = ""
    for i in range(file_nums):
        if i == 0:
            inputFile = f"{input_prefix}/data.txt"
        else:
            inputFile += f",{input_prefix}/data{i}.txt"


    # 构造要发送的任务消息，包含任务的各种路径和相关信息
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

    # 发送消息到队列中，消息内容转换为UTF-8编码的字节流
    channel.basic_publish(exchange="", routing_key=queue_name, body=message_json.encode(encoding="utf-8"))

    # 关闭连接
    connection.close()

    # 打印任务提交成功的消息
    print_green(f"任务{task_id}已提交")

