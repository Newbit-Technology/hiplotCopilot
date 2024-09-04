from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI


def chat_openai(temperature=0):
    return ChatOpenAI(
        model="gpt-4o-2024-08-06",
        openai_api_key="sk-A9TX4JVVEEotW5JHAe186fCeBf6c4b06A7Dc5a2f2bB213F2",
        openai_api_base="https://api.gpt.ge/v1",
        temperature=temperature,
        max_tokens=8000,
    )


def chat_claude(temperature=0):
    return ChatOpenAI(
        model="claude-3-5-sonnet-20240620",
        openai_api_key="sk-A9TX4JVVEEotW5JHAe186fCeBf6c4b06A7Dc5a2f2bB213F2",
        openai_api_base="https://api.gpt.ge/v1",
        temperature=temperature,
        max_tokens=8000,
    )


def gemini_openai(temperature=0):
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash-exp-0827",
        api_key="AIzaSyDSPmeGIwE8J0NBRNFpxbVtiemhdxQryOA",
        temperature=temperature,
        max_tokens=8000,
    )


import base64
from langchain_core.messages import HumanMessage


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def encode_image_message(descirbe, image_path):
    image_data = encode_image(image_path)
    message = HumanMessage(
        content=[
            {"type": "text", "text": f"{descirbe}"},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_data}"},
            },
        ]
    )
    return message
