# import subprocess
import requests
import google.generativeai as genai
import json
import time
import threading
import re

from flask import Flask, request
from Gemini_tone_module import generate_style_response
from dataclasses import dataclass, asdict
from typing import Dict

from constants import VERIFY_TOKEN, PAGE_ACCESS_TOKEN, GEMINI_API_KEY

# Load reply texts from json file
with open("replies.json", "r", encoding="utf-8") as file:
    REPLIES = json.load(file)
    VALID_TONES = list(REPLIES["VALID_TONES"].keys())
    VALID_RESPONDS = list(REPLIES["VALID_RESPONDS"].keys())


def get_reply(msg_dict_key: str) -> str:
    """Returns a predefined reply. If not found, prints an error message."""
    if msg_dict_key in VALID_TONES:
        return REPLIES["VALID_TONES"][msg_dict_key]

    elif msg_dict_key in VALID_RESPONDS:
        return REPLIES["VALID_RESPONDS"][msg_dict_key]

    else:
        error_msg = f"⚠️ ERROR: '{msg_dict_key}' not found in replies.json!"
        print(error_msg)  # Directly print error message
        return "❓ Unknown message type."


# ---------------------------------

# Initialize Gemini for location analysis
genai.configure(api_key=GEMINI_API_KEY)
model_location = genai.GenerativeModel("gemini-2.5-flash")


# ---------------------------------
# User_data management
@dataclass
class UserInfo:
    user_id: str
    reels_content: str
    store_name: str = ""
    tone_type: str = ""
    location_false_time: int = 0
    is_tone_selected: bool = False
    is_reels_provided: bool = False
    is_store_correct: bool = False


USER_DATA_FILE = "user_data.json"
user_data: Dict[str, UserInfo] = {}


# Load data from file when program starts
def load_user_data():
    global user_data
    try:
        with open(USER_DATA_FILE, "r", encoding="utf-8") as user_data_file:
            data = json.load(user_data_file)

            # 過濾掉不是 UserInfo 欄位的部分
            def filter_user_info(info_dict):
                allowed_keys = UserInfo.__dataclass_fields__.keys()
                return {k: v for k, v in info_dict.items() if k in allowed_keys}

            user_data = {
                user_id: UserInfo(**filter_user_info(user_info))
                for user_id, user_info in data.items()
            }

    except (FileNotFoundError, json.JSONDecodeError):
        user_data = {}


# Background function to save periodically (runs in a separate thread)
def auto_save_user_data():
    while True:
        time.sleep(30)  # Save every 30 seconds
        with open(USER_DATA_FILE, "w", encoding="utf-8") as user_data_file:
            json.dump({user_id: asdict(user) for user_id, user in user_data.items()}, user_data_file, indent=4)
            print("✅ User data saved!")


# Function to retrieve user data
def get_user_data(user_id: str) -> UserInfo:
    return user_data.get(user_id, None)


threading.Thread(target=auto_save_user_data, daemon=True).start()

# Load existing data on startup
load_user_data()


# ---------------------------------
# Functions

def print_status(line: str, user_id: str | None = None) -> None:
    if user_id is None:
        print(line)
    else:
        print(f"{user_id}: \n{line}")


def show_user_data(user_id: str) -> str:
    attrs = vars(get_user_data(user_id=user_id))
    text = ', '.join("%s: %s" % item for item in attrs.items())
    print(attrs)
    return text


def create_or_update_user_and_reel(user_id: str, reels_content: str | None) -> bool:
    """
        This function determine if the user exist.
        If he does, updating his reels_content. Otherwise, adding to a new member.

        :param user_id: 16-digit num (save as str)
        :param reels_content:

        :return: True if updating user, False if adding user
    """
    user = get_user_data(user_id)
    if user is not None:
        # 💡 若使用者傳來新的 reels，視為重啟一個新的分析流程，重設所有資料
        if reels_content is not None:
            user.reels_content = reels_content
            user.store_name = ""
            user.tone_type = ""
            user.location_false_time = 0
            user.is_tone_selected = False
            user.is_reels_provided = True
            user.is_store_correct = False
        print_status(user_id=user_id, line="User exist, resetting user info and updating reels_content.")
        return True
    else:
        # Adding to a new user
        user_data[user_id] = UserInfo(user_id=user_id, reels_content=reels_content, is_reels_provided=True)
        print_status(user_id=user_id, line="User not found, adding to a new member.")
        return False


def delete_user_reel(user_id: str) -> None:
    """
        This function check if user exist and safely delete the user from data.

        :param user_id: user_id (16-digit num)
        :return: None
    """
    if user_id in user_data:
        del user_data[user_id]
        print_status(user_id, "User Deleted.")
    else:
        print_status(user_id, "User Not Found")


# Gemini 分析地點功能
def fetch_location_info_from_gemini(reels_content: str) -> (str, str):
    """
        This function using Gemini to analyze the reels_content
        and reply, asking if it fetches the correct place info.

        :param reels_content: user's reels_content
        :return: The Reply (answer) from Gemini and asking question.
    """

    def location_info_from_gemini(prmpt: str) -> str:
        """
            This function ask Gemini to reply the location info

            :param prmpt: prompt for Gemini
            :return: the response of Gemini
        """

        print_status(line="📡 呼叫 Gemini 取得地點資訊...")
        response = model_location.generate_content(prmpt)
        return response.text.strip()

    prompt = f"""
        Please extract the location or store name from the following text.
        Text: {reels_content}

        Search the content for store names and addresses.
        If no store name is found, reply with “No store name information.”
        If no address is found, reply with “No address information.”
        The store name should be unique. If it is a chain store, list multiple addresses as bullet points.
        Do not over-explain. Only provide the store name and address.
        If both the store name and the address cannot be found, reply with “Not found.”
        Response format:

        【Store Name】：(store name, unique)
        【Address】：(address; if multiple addresses exist, list them as bullet points)
        """
    reply = location_info_from_gemini(prompt)

    # Store the store name
    match = re.search(r"【店名】\s*[:：]\s*(.+)", reply)

    if match:
        store_name = match.group(1)  # get store name
        return store_name, reply + "\n\nIs this the location you were looking for?"
    else:
        return "NO", "Sorry, I couldn’t find any clear store information😢 If you’d like, I can try analyzing it again."


# User send a plain text
def plain_text_flow(recipient_id, message_text) -> str | None:
    print("plain_text_flow")
    print(recipient_id, message_text)

    return "Sorry, I only accept Reels content and quick-reply buttons!"


# User respond a quick_reply
def quick_reply_flow(recipient_id, msg_payload) -> str | None:
    print("quick_reply_flow")
    print(recipient_id, msg_payload)

    current_user = get_user_data(recipient_id)

    # User exist
    if current_user is not None:

        # Clean the reels user provided
        if msg_payload == "WANT_TO_END_DIALOG":
            # delete_user_reel(recipient_id)
            current_user.reels_content = ""
            current_user.store_name = ""
            current_user.is_reels_provided = False
            return "Thank you for using this service! Feel free to send me Reels anytime! 🌟"

        elif msg_payload == "FORCE_TREAT_AS_FOOD":
            current_user = get_user_data(recipient_id)
            store_name, message_to_ig = fetch_location_info_from_gemini(current_user.reels_content)

            if store_name == "NO":
                # 無法找到店名，改為顯示「再試一次」選項
                send_ig_quick_reply(recipient_id, message_to_ig, ["TRY_AGAIN_LOCATION", "WANT_TO_END_DIALOG"])
            else:
                # 正常流程
                current_user.store_name = store_name
                send_ig_quick_reply(recipient_id, message_to_ig, ["YES", "NO", "WANT_TO_END_DIALOG"])

            return None

        elif msg_payload == "TRY_AGAIN_LOCATION":
            current_user = get_user_data(recipient_id)

            # 增加錯誤次數
            current_user.location_false_time += 1

            # 如果嘗試次數 >= 2，則直接結束
            if current_user.location_false_time >= 2:
                current_user.location_false_time = 0  # reset
                message_to_ig = "Sorry, I still couldn’t extract the location😣\n\nPlease try re-uploading or provide a Reels with clearer details. Thank you!"
                send_ig_quick_reply(recipient_id, message_to_ig, ["WANT_TO_END_DIALOG"])
                return None

            # 否則再試一次 fetch
            store_name, message_to_ig = fetch_location_info_from_gemini(current_user.reels_content)

            if store_name == "NO":
                short_message = "Sorry, I couldn’t find any clear store information😢 Do you want me to try analyzing it again?"
                send_ig_quick_reply(
                    recipient_id,
                    short_message,
                    ["TRY_AGAIN_LOCATION", "WANT_TO_END_DIALOG"]
                )

            else:
                # 終於找到了
                current_user.store_name = store_name
                send_ig_quick_reply(recipient_id, message_to_ig, ["YES", "NO", "WANT_TO_END_DIALOG"])

            return None

        # Valid way to change tone
        if msg_payload in VALID_TONES:
            change_tone(user_id=recipient_id, tone_type=msg_payload)

        # Want/need to change tone
        elif msg_payload == "WANT_TO_CHANGE_TONE" or not current_user.is_tone_selected:
            let_user_change_tone(user_id=recipient_id)

        # Correct place is given by Gemini
        elif msg_payload == "YES":
            print("✅ Gemini 風格回覆即將產生！")
            current_user.is_store_correct = True

        # Wrong place is given by Gemini
        elif msg_payload == "NO":
            current_user.location_false_time += 1
            current_user.is_store_correct = False

        # Tone and reels are set up
        if current_user.is_tone_selected and current_user.is_reels_provided:

            # Stor is correct (all set up) -> Generate response
            if current_user.is_store_correct:
                styled_reply = generate_style_response(current_user.store_name, current_user.reels_content,
                                                       current_user.tone_type)
                if "請求次數已超過" in styled_reply:
                    send_ig_message(recipient_id, styled_reply)
                    return None
                send_ig_message(recipient_id, styled_reply)
                current_user.location_false_time = 0
                # Tell user he/she can change tone
                send_ig_message(recipient_id, f"📢 If you want to adjust the tone, please click 【{get_reply('WANT_TO_CHANGE_TONE')}】! 😊")

                # Teach user how to end dialog
                send_ig_quick_reply(recipient_id, f"⚠️ If you want to end the conversation, you can click 【{get_reply('WANT_TO_END_DIALOG')}】",
                                    ['WANT_TO_CHANGE_TONE', 'WANT_TO_END_DIALOG'])

            # Store is not correct -> fetch other information
            else:
                if current_user.location_false_time < 3:
                    # 先 fetch，再根據結果處理
                    current_user.store_name, message_to_ig = fetch_location_info_from_gemini(current_user.reels_content)

                    if current_user.store_name == "NO":
                        short_message = "Sorry, I couldn’t find any clear store information😢\n\nDo you want me to try analyzing it again?"
                        send_ig_quick_reply(
                            recipient_id,
                            short_message,
                            ["TRY_AGAIN_LOCATION", "WANT_TO_END_DIALOG"]
                        )
                    else:
                        send_ig_quick_reply(recipient_id, message_to_ig, ["YES", "NO", "WANT_TO_END_DIALOG"])

                else:
                    message_to_ig = "Sorry, I couldn’t extract the location. Please try re-uploading or provide a Reels with more detailed information. Thank you!"
                    current_user.location_false_time = 0
                    send_ig_quick_reply(recipient_id, message_to_ig, ["WANT_TO_END_DIALOG"])

            return None

    # User Not Exist
    else:
        return "Please send me the Reels you want to check so we can start the conversation~"


# 檢查 reels_content 是否與食物相關
def is_food_related(reels_content: str) -> bool:
    prompt = f"""
            You are a classifier specialized in detecting whether a text is related to food-related content.

            Please determine whether the following text is NOT related to “food recommendations or introductions.”

            If you detect that more than 70% of the content is not related to food recommendations or introductions, reply “No.”

            Your task is to judge whether this text was written by a food blogger sharing or introducing food.

            If the content includes phrases about DIY tutorials or how to make something, reply “No.”

            If the content includes memes, entertainment, or similar elements, reply “No.”

            If the content includes store names, phone numbers, business hours, or phrases like “XX shop,”
            and if your initial judgment was “No,” change your answer to “Yes.”

            Please reply with only “Yes” or “No,” without adding any additional text.

            Below is the text:
            {reels_content}
            """
    print("📡 呼叫 Gemini 進行食物分類判斷...")
    response = model_location.generate_content(prompt)
    result = response.text.strip().replace("。", "")
    return result == "Yes"



def send_ig_message(recipient_id, reply_text):
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    headers = {"Content-Type": "application/json"}

    if len(reply_text) > 1900:
        reply_text = reply_text[:1900] + "...（訊息過長已截斷）"

    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": reply_text},
        "messaging_type": "UPDATE"
    }
    requests.post(url, json=payload, headers=headers)
    # print("📤 發送狀態碼:", response.status_code)
    # print("📤 發送回應內容:", response.text)


def send_ig_quick_reply(recipient_id, message_text, options):
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    headers = {"Content-Type": "application/json"}

    quick_replies = [{
        "content_type": "text",
        "title": get_reply(option),
        "payload": option
    } for option in options]

    payload = {
        "recipient": {"id": recipient_id},
        "message": {
            "text": message_text,
            "quick_replies": quick_replies
        },
        "messaging_type": "RESPONSE"
    }

    # response
    requests.post(url, json=payload, headers=headers)
    # print("📤 發送狀態碼:", response.status_code)
    # print("📤 發送回應內容:", response.text)


def user_setups_are_all_set(user_id: str, message_text: str | None) -> bool:
    create_or_update_user_and_reel(user_id=user_id, reels_content=message_text)
    user = get_user_data(user_id=user_id)

    return user.is_reels_provided and user.is_tone_selected and user.is_store_correct


def let_user_change_tone(user_id: str) -> None:
    get_user_data(user_id=user_id).is_tone_selected = False
    message_to_ig = "Which tone would you like me to use in future replies 🤖? \n\nPlease choose:" + "、".join(map(get_reply, VALID_TONES))
    send_ig_quick_reply(user_id, message_to_ig, VALID_TONES + ["WANT_TO_END_DIALOG"])


def change_tone(user_id: str, tone_type: str) -> None:
    if tone_type in VALID_TONES:

        user = get_user_data(user_id=user_id)
        user.tone_type = tone_type
        user.is_tone_selected = True
        print_status(user_id=user_id, line=f"✅ User-selected tone:{user.tone_type}")

    else:
        print_status(user_id=user_id, line=f"⚠️ERROR: Unexpected error when changing tone!")


app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("✅ 驗證成功！Webhook 已連接。")
            return challenge, 200
        else:
            print("❌ 驗證失敗。請確認 VERIFY_TOKEN 是否一致。")
            return "驗證失敗", 403

    elif request.method == "POST":
        data = request.get_json()
        # message_text = ""

        # reply_text = ""
        # sender_id = None

        if "entry" in data:
            for entry in data["entry"]:
                for messaging_event in entry.get("messaging", []):
                    sender_id = messaging_event["sender"]["id"]

                    if "message" in messaging_event:

                        if messaging_event["message"].get("is_echo", False):
                            print("Message from ourselves")
                            continue

                        # Got an attachment (might be a reel or a post)
                        if "attachments" in messaging_event["message"]:
                            print("Got an attachment")

                            for attachment in messaging_event["message"]["attachments"]:
                                print("🧩 Attachment type:", attachment["type"])  # 👈 加這行來 debug
                                # Get a reel or post from user
                                if attachment["type"] == "ig_reel":
                                    message_text = attachment["payload"].get("title", "(沒有標題)")

                                    if not is_food_related(message_text):
                                        text = ("Sorry 😅！\n\nBased on my initial judgment, this Reels doesn’t seem to be food-related 🍽️, so I’m unable to retrieve store information.\n\nIf this is actually a food-related Reels, please click the button 【This is a food Reels】 and I’ll immediately help you find the store information! 🏃‍♂️💨")
                                        create_or_update_user_and_reel(sender_id, reels_content=message_text)
                                        send_ig_quick_reply(sender_id, text,
                                                            ["FORCE_TREAT_AS_FOOD", "WANT_TO_END_DIALOG"])

                                    else:
                                        # Save the attachment info in the first place (user_setups_are_all_set()) is
                                        # user_setups_are_all_set() ? True -> fetch location info and ask if the
                                        # place is right
                                        if user_setups_are_all_set(user_id=sender_id, message_text=message_text):
                                            user = get_user_data(user_id=sender_id)
                                            user.store_name, message_to_ig = fetch_location_info_from_gemini(
                                                get_user_data(user_id=sender_id).reels_content)
                                            if user.store_name == "NO":
                                                send_ig_quick_reply(sender_id, message_to_ig,
                                                                    ["TRY_AGAIN_LOCATION", "WANT_TO_END_DIALOG"])

                                            else:
                                                send_ig_quick_reply(sender_id, message_to_ig,
                                                                    ["YES", "NO", "WANT_TO_END_DIALOG"])

                                        # User didn't select the tone -> act as want to change tone
                                        else:
                                            let_user_change_tone(user_id=sender_id)

                                else:
                                    reply_text = "⚠️Sorry, I’m currently unable to process IG posts or any content that isn’t a Reels～ Please try sending me another piece of content, and I’ll do my best to look it up for you! 📹💬"
                                    send_ig_message(recipient_id=sender_id, reply_text=reply_text)

                        # User respond a quick reply
                        elif "quick_reply" in messaging_event["message"]:
                            quick_reply_payload = messaging_event["message"]["quick_reply"]["payload"]
                            reply_text = quick_reply_flow(recipient_id=sender_id, msg_payload=quick_reply_payload)
                            if reply_text is not None:
                                send_ig_message(recipient_id=sender_id, reply_text=reply_text)
                            return "OK", 200

                        # Got plain text (No reels or posts included) -> may want to change tone or say yes/no to Gemini
                        elif "text" in messaging_event["message"]:
                            message_text = messaging_event["message"]["text"]
                            reply_text = plain_text_flow(recipient_id=sender_id, message_text=message_text)
                            send_ig_message(recipient_id=sender_id, reply_text=reply_text)
                            send_ig_message(recipient_id=sender_id, reply_text="Please resend the Reels to start the conversation.")

                        # Unexpected messaging_event (not reels, not posts, not plain text)
                        else:
                            reply_text = "⚠️ Unrecognized message type"
                            send_ig_message(recipient_id=sender_id, reply_text=reply_text)

                    return "OK", 200

        return "OK", 200

    # ✅ ADD THIS FINAL RETURN STATEMENT as a fallback
    return "Webhook endpoint reached.", 200


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))  # Render provides this
    app.run(host="0.0.0.0", port=port)
