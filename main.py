
import os
import logging
from playwright.async_api import async_playwright
from telegram.ext import Application, CommandHandler

# ------------------------------
# Logging (debug လိုရင် အထောက်ကူ)
# ------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------------
# Replit (သို့ VPS) စသဖြင့် Environment ထဲက Secrets
# ------------------------------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
LOGIN_EMAIL = os.environ.get("LOGIN_EMAIL")
LOGIN_PASSWORD = os.environ.get("LOGIN_PASSWORD")

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN env missing")
if not LOGIN_EMAIL or not LOGIN_PASSWORD:
    logger.warning("LOGIN_EMAIL or LOGIN_PASSWORD not set - login may fail")

# ------------------------------
# ငါ့ VPN Keygen Page URL
# Login / Dashboard 2 လုံး တစ်ပုံတည်း သုံးထားမယ်
# ------------------------------
LOGIN_URL = "http://saikokowinmyanmar123.com/KEYGEN/index.php"
DASHBOARD_URL = "http://saikokowinmyanmar123.com/KEYGEN/index.php"

# ------------------------------
# Playwright Global vars
# ------------------------------
_pw = None
_browser = None
_page = None


async def get_page():
    """
    Playwright browser + page ကို 1 ကြိမ်ပဲ ဖွင့်မယ်
    နောက် command တွေအတွက် reuse လုပ်မယ်
    """
    global _pw, _browser, _page
    if _page is None:
        _pw = await async_playwright().start()
        _browser = await _pw.chromium.launch(headless=True)
        _page = await _browser.new_page()
        logger.info("Browser launched")
    return _page


async def close_browser():
    """ /stop ပို့လို့ browser ပိတ်ချင်တဲ့အခါ သုံးမယ့် function """
    global _pw, _browser, _page
    try:
        if _browser:
            await _browser.close()
            logger.info("Browser closed")
        if _pw:
            await _pw.stop()
            logger.info("Playwright stopped")
    finally:
        _pw = None
        _browser = None
        _page = None


# =========================
#  LOGIN ACTION
# =========================
async def do_login():
    page = await get_page()
    logger.info("Opening login page...")
    await page.goto(LOGIN_URL)

    # ဒီ selector တွေ မတိရင်နောက်ထပ် HTML ပို့ပေးရင် ငါပြင်ပေးရမယ်
    # ရှိနိုင်သလို generic selector ဖြင့် စ til စမ်းထားတယ်
    try:
        await page.fill("input[name='email'], input#email, input[type='email']", LOGIN_EMAIL)
        await page.fill("input[name='password'], input#password, input[type='password']", LOGIN_PASSWORD)
        await page.click(
            "button[type='submit'], input[type='submit'], button#login, .btn-login"
        )
        logger.info("Login submitted")
    except Exception as e:
        logger.error(f"Login selectors error: {e}")
        raise

    await page.wait_for_timeout(2000)  # 2 sec


# =========================
#  AUTO CLICK KEYGEN
# =========================
async def do_auto_click():
    page = await get_page()
    logger.info("Opening dashboard for auto click...")
    await page.goto(DASHBOARD_URL)

    # ဒီ selector ကို မင်းရဲ့ keygen button ID/class နဲ့ မတိရင် နောက်ထပ် ပြင်နိုင်
    # ဥပမာ #generate / .btn-primary ...
    for i in range(10):  # 10 ခါ click (လိုသလို ပြင်လို့ရ)
        try:
            await page.click(
                "#generate, button#generate, button.generate, button.btn-primary"
            )
            logger.info(f"Generate button clicked {i+1} times")
        except Exception as e:
            logger.error(f"Generate click error on loop {i+1}: {e}")
            break

        await page.wait_for_timeout(1500)  # 1.5 sec


# =========================
#  TELEGRAM COMMAND HANDLERS
# =========================
async def cmd_start(update, context):
    await update.message.reply_text(
        "VPN Keygen Bot Online 😎\n"
        "/login - login to panel\n"
        "/click - auto generate keys\n"
        "/stop - close browser"
    )


async def cmd_login(update, context):
    await update.message.reply_text("🔐 Logging in to keygen panel...")
    try:
        await do_login()
        await update.message.reply_text("✅ Login OK (selectors မှန်ရင်)")
    except Exception as e:
        await update.message.reply_text(f"❌ Login error: {e}")


async def cmd_click(update, context):
    await update.message.reply_text("▶️ Auto keygen clicking starting...")
    try:
        await do_auto_click()
        await update.message.reply_text("✅ Auto click loop finished.")
    except Exception as e:
        await update.message.reply_text(f"❌ Auto click error: {e}")


async def cmd_stop(update, context):
    await close_browser()
    await update.message.reply_text("🛑 Browser closed")


# =========================
#  MAIN (Telegram bot runner)
# =========================
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("login", cmd_login))
    app.add_handler(CommandHandler("click", cmd_click))
    app.add_handler(CommandHandler("stop", cmd_stop))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
