import json
import string

import nanoid
from flask import Flask, request, Response
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage, SystemMessage

from common.print_color import print_red, print_yellow, print_green
from pipeline.copilot import TalkHelper
talk_helper = TalkHelper()
app = Flask(__name__)
def lang_chain_with_function_calling(user_message):
    # 初始化消息列表，包含用户的第一条消息
    # 使用语言模型预测回复消息，同时提供可调用的函数列表
    print(user_message)

    # 转换消息列表
    langchain_messages = []
    for msg in user_message:
        if msg['role'] == 'system':
            langchain_messages.append(SystemMessage(content=msg['content']))
        elif msg['role'] == 'user':
            langchain_messages.append(HumanMessage(content=msg['content']))
        elif msg['role'] == 'assistant':
            langchain_messages.append(AIMessage(content=msg['content']))
        elif msg['role'] == 'function':
            langchain_messages.append(ToolMessage(name=msg['name'], content=msg['content']))


    func_message = talk_helper.func_llm.invoke(langchain_messages)
    print_green(func_message)
    # 检查模型是否返回了需要调用函数的附加参数
    if "tool_calls" in func_message.additional_kwargs:
        # 获取需要调用的函数名称和参数
        print_yellow(f"{func_message.additional_kwargs}")
        function_name = func_message.additional_kwargs["tool_calls"][0]["function"]['name']
        arguments = json.loads(func_message.additional_kwargs["tool_calls"][0]["function"]['arguments'])
        function_response = talk_helper.func_call(function_name, arguments)
        # 初始化函数执行结果字符串
        print_yellow(f"{function_name}:{arguments}")
        print_yellow(function_response)
        function_message = ToolMessage(name=function_name, content=function_response)
        # 将函数执行结果消息添加到消息列表中
        langchain_messages.append(function_message)

        # 再次使用语言模型预测回复消息，提供可调用的函数列表
        second_response = talk_helper.func_llm.invoke(langchain_messages)
        # 返回最终的AI回复
        return second_response.content
    else:
        # 如果不需要调用函数，直接返回模型生成的回复
        return func_message.content


@app.route('/chat/completions', methods=['POST'])
def chat():
    # 从请求中获取用户消息
    print(request.json)
    user_message = request.json.get('messages')
    # 自定义回复逻辑
    assistant_message = lang_chain_with_function_calling(user_message)
    import time
    # 构造 OpenAI API 兼容的回复格式
    def generate():
        # 构造 OpenAI API 兼容的流式回复格式
        nonlocal assistant_message
        for i, message_part in enumerate(assistant_message):
            response = {
                "id": nanoid.generate(alphabet=string.digits + string.ascii_letters, size=10),  # 自定义 ID
                "object": "chat.completion.chunk",
                "created": int(time.time()),  # 自定义时间戳
                "model": "BioChat",  # 使用的模型
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "role": "assistant",
                            "content": message_part
                        },
                        "finish_reason": None if i < len(assistant_message) - 1 else "stop"
                    }
                ]
            }
            yield f"data: {json.dumps(response, ensure_ascii=False)}\n\n"
            time.sleep(0.005)  # 模拟延迟

    return Response(generate(), content_type='text/event-stream')



if __name__ == '__main__':
    app.run(debug=False)


