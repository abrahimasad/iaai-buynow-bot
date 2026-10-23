import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

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
    
    async with async_playwright() as p:
        print("جاري تشغيل المتصفح الخفي...")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            print("جاري فتح صفحة IAAI...")
            await page.goto(SEARCH_URL, wait_until="networkidle", timeout=60000)
            
            # استخراج بيانات JSON من داخل الصفحة
            data = await page.evaluate("() => window.__PRELOADED_STATE__")
            
            if not data:
                print("لم يتم العثور على بيانات السيارات في الصفحة (المتغير غير موجود).")
                await browser.close()
                return
                
            vehicles = data.get('search', {}).get('results', {}).get('vehicles', [])
            print(f"تم العثور على {len(vehicles)} سيارة في الصفحة.")
            
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
                print(f"تم إرسال {new_count} سيارة جديدة.")
            else:
                print("لا توجد سيارات جديدة.")
                
        except Exception as e:
            print(f"حدث خطأ: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
