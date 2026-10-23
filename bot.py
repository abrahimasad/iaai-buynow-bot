import asyncio
import json
import os
import re
from datetime import datetime
from playwright.async_api import async_playwright

# الإعدادات (يجب أن تكون موجودة في متغيرات البيئة)
TELEGRAM_TOKEN = "8753580180:AAGeqNP2i7Mz2HPTe1yz4btCEdQ3s4egsdY"
TELEGRAM_CHAT_ID = "-1004331051453"

SEARCH_URL = "https://ca.iaai.com/search?url=VsoyNCWV1wQJY1OShrTHQEFSOrymOTM4goP8Gtj6oppB/Z5bU4Gie3t/N19YKgq7ORCvsXylBZephKBNJ2p4WYRjbPTOZ1O5j46ZcpX0="

BASE_DIR = os.path.join(os.path.expanduser("~"), "IAAI_BuyNow_Bot")
VEHICLES_DIR = os.path.join(BASE_DIR, "vehicles")
SEEN_FILE = os.path.join(BASE_DIR, "seen_vehicles.json")

def setup_dirs():
    os.makedirs(VEHICLES_DIR, exist_ok=True)

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f)

# دالة إرسال الرسائل إلى تيليجرام
def send_telegram(text):
    import requests
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        requests.post(url, json=payload, timeout=15)
    except Exception as e:
        print(f"Telegram Error: {e}")

def save_txt_file(v, vin_masked):
    stock_id = str(v.get("StockId", ""))
    year = v.get("Year", "")
    make = v.get("Make", "")
    model = v.get("Model", "")
    car_name = f"{year} {make} {model}".strip()
    
    content = f"""Status: ADDED
VIN Status: pending

Stock: {v.get('StockNum', '')}
StockId: {stock_id}
VIN Masked: {vin_masked}
Full VIN:

Year: {year}
Make: {make}
Model: {model}

Damage: {v.get('Damage', '')}
Secondary Damage: {v.get('SecondaryDamage', '')}
Location: {v.get('Location', '')}

Odometer: {v.get('Odometer', '')}
Transmission: {v.get('Transmission', '')}
Engine: {v.get('Engine', '')}
Fuel Type: {v.get('FuelType', '')}
Keys: {v.get('Keys', '')}
Drives: {v.get('Drives', '')}
Starts: {v.get('Starts', '')}
Condition: {v.get('Condition', '')}
Brand Code: {v.get('BrandCode', '')}
Brand: {v.get('Brand', '')}

Vehicle URL:
https://ca.iaai.com/vehicle-details/{stock_id}
{car_name}

Auction Date: {v.get('AuctionDate', '')}
Auction Date UTC: 
Auction Lane: {v.get('AuctionLane', '')}
Auction Sequence: {v.get('AuctionSequence', '')}
Auction Type: {v.get('AuctionType', '')}
Sale Status: 
High Prebid: 
Damage Estimate: {v.get('DamageEstimate', '')}

Collected At: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Image URLs:
"""
    for i in range(1, 21):
        content += f"https://vis.iaai.com/resizer?imageKeys={v.get('ImageKey', '')}~SID~B1~S0~I{i}&width=1600&height=1200\n"

    file_path = os.path.join(VEHICLES_DIR, f"{stock_id}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

async def main():
    setup_dirs()
    seen = load_seen()
    
    send_telegram("🔄 <b>بدء دورة مراقبة جديدة...</b>")

    async with async_playwright() as p:
        send_telegram("🌐 جاري فتح المتصفح الخفي...")
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        
        page = await context.new_page()
        
        try:
            send_telegram("⏳ جاري تحميل موقع IAAI (انتظار 15 ثانية)...")
            await page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(15) # انتظار أطول للحماية
            
            data = await page.evaluate("() => window.__PRELOADED_STATE__")
            
            if not data:
                html_content = await page.content()
                send_telegram(f"⚠️ <b>لم يتم العثور على البيانات!</b>\nطول صفحة HTML: {len(html_content)} حرف.\nقد تكون الحماية ما زالت تمنعنا.")
                await browser.close()
                return
                
            vehicles = data.get('search', {}).get('results', {}).get('vehicles', [])
            send_telegram(f"✅ <b>تم قراءة الصفحة بنجاح!</b>\nعدد السيارات الموجودة: {len(vehicles)}")
            
            new_count = 0
            for v in vehicles:
                stock_id = str(v.get("StockId", ""))
                if not stock_id or stock_id in seen:
                    continue

                vin_masked = v.get("VIN", "") or v.get("Vin", "")
                save_txt_file(v, vin_masked)
                
                msg = (
                    f"🚨 <b>سيارة Buy Now جديدة!</b>\n\n"
                    f"🚗 <b>{v.get('Year', '')} {v.get('Make', '')} {v.get('Model', '')}</b>\n"
                    f"🆔 Stock: <code>{stock_id}</code>\n"
                    f"🔑 VIN: <code>{vin_masked}</code>\n"
                    f"💰 Buy Now: {v.get('BuyNowPrice', '')}\n"
                    f"📍 {v.get('Location', '')}\n"
                    f"🔗 <a href='https://ca.iaai.com/vehicle-details/{stock_id}'>اضغط لفتح السيارة</a>"
                )
                send_telegram(msg)
                seen.add(stock_id)
                new_count += 1

            if new_count > 0:
                save_seen(seen)
                send_telegram(f"🎉 <b>تم إرسال {new_count} سيارة جديدة بنجاح.</b>")
            else:
                send_telegram("ℹ️ لا توجد سيارات جديدة في هذه الدورة.")
                
        except Exception as e:
            send_telegram(f"❌ <b>حدث خطأ تقني:</b>\n{e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
