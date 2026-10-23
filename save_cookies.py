import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # فتح متصفح مرئي (غير مخفي) لكي تراه بعينك
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("جاري فتح الموقع... يرجى الانتظار.")
        await page.goto("https://ca.iaai.com/")
        
        print("\n" + "="*50)
        print("المتصفح مفتوح الآن أمامك.")
        print("1. قم بتسجيل الدخول (إذا لزم الأمر).")
        print("2. تأكد من أنك تستطيع رؤية صفحة Buy Now والسيارات.")
        print("3. بعد الانتهاء، ارجع إلى هذه الشاشة السوداء واضغط Enter.")
        print("="*50 + "\n")
        
        # انتظار حتى تضغط Enter في الشاشة السوداء
        input("اضغط Enter هنا بعد الانتهاء من المتصفح...")

        # حفظ الكوكيز
        cookies = await context.cookies()
        import json
        with open("cookies.json", "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=4)
        
        print("تم حفظ الكوكيز بنجاح في ملف cookies.json!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
