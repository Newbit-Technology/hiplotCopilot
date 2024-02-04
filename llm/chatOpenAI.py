from langchain_openai import ChatOpenAI

def chat_openai(temperature=0):
    return ChatOpenAI(
    model='deepseek-chat',
    openai_api_key='sk-e884df8670e544a8b7d0c765760f2c19',
    openai_api_base='https://api.deepseek.com/beta',
    temperature=0.0,
    max_tokens=8000,
    )