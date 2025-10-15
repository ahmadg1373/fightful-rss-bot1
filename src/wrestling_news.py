# -*- coding: utf-8 -*-
import feedparser
import requests
import json
from bs4 import BeautifulSoup

CONFIG = {
    "RSS_FEED": "https://www.fightful.com/wrestling/rss",
    "OPENROUTER_API_KEY": "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",
    "TELEGRAM_BOT_TOKEN": "8462093442:AAFsGqk7O0jrrUv_qdI_-HoEvQOYnRRJbVo",
    "TELEGRAM_CHANNEL": "@wrestlingnewsauto",
    "RESULT_FILE": "result_output.txt"
}

def get_latest_article_link():
    feed = feedparser.parse(CONFIG["RSS_FEED"])
    if not feed.entries:
        print("❌ فید خبری خالی است.")
        return None
    link = feed.entries[0].link
    print("✅ لینک خبر پیدا شد:", link)
    return link

def scrape_article_content(url):
    try:
        response = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    except Exception as e:
        print("❌ خطا در دریافت:", str(e))
        return None
    if response.status_code != 200:
        print("❌ دریافت صفحه با خطا:", response.status_code)
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else "بدون عنوان"
    content_div = soup.find("div", {"class": "field-item"}) or soup.find("article")
    content = content_div.get_text(separator="\n", strip=True) if content_div else None

    if not content or len(content) < 200:
        print("⚠️ محتوای کافی یافت نشد.")
        return None

    print("✅ متن مقاله با موفقیت دریافت شد.")
    return {"title": title, "content": content, "url": url}

def process_with_ai(data):
    print("🤖 در حال پردازش متن با هوش مصنوعی و بازنویسی پیشرفته ...")
    try:
        prompt = (
            "به‌عنوان یک خبرنگار فارسی‌زبان حرفه‌ای، متن زیر را بازنویسی کن و خروجی را "
            "با ساختار انسانی ارائه بده. ساختار خروجی باید شامل پنج بخش با ایموجی‌های زیر باشد:\n"
            "📰 عنوان خبر\n📌 خلاصه کوتاه\n✍️ بازنویسی متن\n🏷 تگ‌ها با کاما جداشده\n🔗 لینک منبع\n\n"
            "در متن بازنویسی از جمله‌پردازی طبیعی و جذاب استفاده کن. از ترجمه تحت‌اللفظی خودداری کن.\n\n"
            "متن خبر:\n"
            + "عنوان: " + data["title"] + "\n\n"
            + data["content"] + "\n\n"
            + "آدرس خبر: " + data["url"]
        )

        headers = {
            "Authorization": "Bearer " + CONFIG["OPENROUTER_API_KEY"],
            "Content-Type": "application/json",
            "HTTP-Referer": "https://fightful.com/",
            "X-Title": "Wrestling News Auto"
        }

        payload = {
            "model": "anthropic/claude-3-haiku",
            "messages": [
                {"role": "system", "content": "You are a helpful and creative Persian journalist assistant."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=90
        )

        if response.status_code != 200:
            print("❌ خطا از API:", response.status_code)
            print("📩 پاسخ کامل:", response.text)
            return None

        data_json = response.json()
        text_output = data_json["choices"][0]["message"]["content"].strip()

        print("✅ پردازش با Claude انجام شد.")
        return text_output
    except Exception as e:
        print("❌ خطا در API:", str(e))
        return None

def save_result_to_file(text):
    try:
        with open(CONFIG["RESULT_FILE"], "a", encoding="utf-8") as f:
            f.write(text)
            f.write("\n" + "-"*80 + "\n")
        print("💾 خروجی در فایل ذخیره شد:", CONFIG["RESULT_FILE"])
    except Exception as e:
        print("❌ خطا در ذخیره:", str(e))

def send_to_telegram(text):
    try:
        url = "https://api.telegram.org/bot" + CONFIG["TELEGRAM_BOT_TOKEN"] + "/sendMessage"
        payload = {
            "chat_id": CONFIG["TELEGRAM_CHANNEL"],
            "text": text,
            "parse_mode": "HTML"
        }
        r = requests.post(url, data=payload, timeout=60)
        if r.status_code == 200:
            print("📨 پیام به تلگرام ارسال شد ✔️")
        else:
            print("❌ ارسال به تلگرام با خطا:", r.text)
    except Exception as e:
        print("❌ خطا در تلگرام:", str(e))

def main():
    link = get_latest_article_link()
    if not link:
        return

    data = scrape_article_content(link)
    if not data:
        return

    ai_result_text = process_with_ai(data)
    if not ai_result_text:
        return

    save_result_to_file(ai_result_text)
    send_to_telegram(ai_result_text)

if __name__ == "__main__":
    print("🚀 شروع فرآیند خودکار خبر ...")
    main()
