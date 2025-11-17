# 🌟 Yummy or Not

A food-review assistant that uses Gemini AI together with IG Reels analysis. It combines online reviews, locations, sentiment evaluation, and tone generation to automatically create introductions that are “expressive, humorous, and emotionally engaging.”

---

## 🚀 Project Features

- Uses Gemini Pro (1.5 & 2.0) to instantly summarize IG Reels content and related online reviews
- Uses Instagram, one of today’s most popular social platforms, as the main interface to increase user reach
- Automatically retrieves food-related reviews from PTT Food Board
- Supports multiple tones: Normal / Meme-style / Emotional / Short
- Expanded introduction features: 😍 Pros, 😓 Cons, 👋 Recommended for

---

## 🛠️ Development Tools and Technologies

- Google Generative AI SDK: Gemini Pro 1.5 / 2.0 for parsing and generating responses
- Meta for Developer (Instagram API): Connects the bot account and reads user messages
- BeautifulSoup: Crawls PTT online reviews
- JSON 資料檔: Stores user activity
- Flask: Backend development, Webhook API main program
- GitHub: Team collaboration and version control
- Render: Deploys the application

---

## 📂 Directory Structure

- `main.py` - Main program that handles Webhook cycles, IG Reels uploads, and quick replies
- `Gemini_tone_module.py` - Contains different tone parsers and Gemini interaction modules
- `style_module.py` - Templates for introduction formats and main prompt management
- `rating_system.py` - Authenticity rating model
- `find_comments_on_web.py` - Scrapes related comments from the PTT Food Board
- `replies.json` - Predefined quick_reply and tone language settings
- `constants.py` - Keys and tokens
- `user_data.json` - Persistent user data storage

---

## ✨ Start the Project

1. Make sure Python >= 3.10 is installed
2. Install the required packages

```bash
pip install -r requirements.txt
```

3. Start the Flask service

```bash
python main.py
```

---

## 🔧 TODO / Future Plan

- [ ] Migrate user data to PostgreSQL for higher persistence and cloud-ready compatibility
- [ ] Integrate more food-review data sources (e.g., Google ratings)
- [ ] Support image recognition of dishes using the Gemini Vision API

---

## ✉️ Contact

If you are interested in this project or want to learn more, feel free to contact us!
Email: yummy2025laili@gmail.com 

