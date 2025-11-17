import json
from constants import GEMINI_API_KEY
import google.generativeai as genai

from find_comments_on_web import find_comments_of_the_place


def load_prompt_from_txt(valid_tone) -> str:
    file_path = f"Prompts/{valid_tone}.txt"
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return "找不到這個 prompt"


# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")
chat = model.start_chat()

# Load reply texts from json file
with open("replies.json", "r", encoding="utf-8") as file:
    REPLIES = json.load(file)
    VALID_TONES = list(REPLIES["VALID_TONES"].keys())
    VALID_RESPONDS = list(REPLIES["VALID_RESPONDS"].keys())


def generate_style_response(store_name: str, store_content: str, tone: str):

    """
    Load the corresponding prompt based on the user-selected tone, and send the request to Gemini.

    """
    if tone not in VALID_TONES:
        return f"⚠️ Unable to find the prompt for '{tone}' style. Please choose another tone."

    # load prompt from txt
    tone_prompt = load_prompt_from_txt(tone)
    print(tone_prompt)

    prompt = (tone_prompt + f"\n\nIntroduce this restaurant: {store_content}" +
              f"Here are some reviews found online that you may refer to: {find_comments_of_the_place(store_name)}" +
              load_prompt_from_txt("COMMON_PROMPT"))
    response = chat.send_message(prompt)

    return response.text.strip()


# 測試
if __name__ == "__main__":
    user_tone = "meme"  # 這裡可以改成 "basic", "short", "formal"...
    result = generate_style_response("世盛一口吃香腸", user_tone)

    # 使用範例
    print(load_prompt_from_txt("meme_tone"))  # 讀取迷因風格

    print(result)
