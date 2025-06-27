from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import os
from duckduckgo_search import DDGS

# Your bot token here
TOKEN = "7438357749:AAH3LA9PSTWBs-yt-xtdGyGLvtCGlcx5Rro"
api_key = "3da3cada9978145e2bc4af49b9dbe71d"  # Numverify API key

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🟢 Welcome to Ruqyah OSINT Bot.\nUse /scan, /plate, /ip, /username, /sim, /address, /photo to begin.")

# /scan <phone> with NumVerify + IPQS
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /scan +91xxxxxxxxxx")
        return

    number = context.args[0]
    await update.message.reply_text(f"🔍 Scanning {number}...")

    try:
        url = f"http://apilayer.net/api/validate?access_key={api_key}&number={number}&country_code=IN&format=1"
        res = requests.get(url)
        data = res.json()

        if not data["valid"]:
            await update.message.reply_text("❌ Invalid number or no data found.")
            return

        ipqs_url = f"https://www.ipqualityscore.com/free-carrier-lookup?phone={number}"
        ipqs_headers = {"User-Agent": "Mozilla/5.0"}
        ipqs_res = requests.get(ipqs_url, headers=ipqs_headers)
        soup = BeautifulSoup(ipqs_res.text, "html.parser")

        score = soup.find("span", class_="badge bg-danger")
        if not score:
            score = soup.find("span", class_="badge bg-warning")
        risk_score = score.text.strip() if score else "Not found"

        result = f"""
📞 Number: {data.get('international_format', 'N/A')}
🧩 Carrier: {data.get('carrier', 'Unknown')} | {data.get('line_type', 'Unknown')}
🌍 Location: {data.get('location', 'Unknown')}
✅ Valid: Yes
⚠️ Risk Score (IPQS): {risk_score}
"""
    except Exception as e:
        result = f"⚠️ Error: {str(e)}"

    await update.message.reply_text(result)

# /plate <regno> with full owner data
async def plate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /plate GJ01AB1234")
        return

    reg = context.args[0].upper()
    await update.message.reply_text(f"🔍 Looking up vehicle: {reg}...")

    try:
        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        r1 = session.get("https://vahan.parivahan.gov.in/nrservices/faces/user/searchstatus.xhtml", headers=headers)
        soup = BeautifulSoup(r1.text, "html.parser")
        viewstate = soup.find("input", {"name": "javax.faces.ViewState"})["value"]

        payload = {
            "javax.faces.partial.ajax": "true",
            "javax.faces.source": "form_rcdl:j_idt43",
            "javax.faces.partial.execute": "form_rcdl:j_idt43 form_rcdl",
            "javax.faces.partial.render": "form_rcdl:j_idt43 form_rcdl",
            "form_rcdl:j_idt43": "form_rcdl:j_idt43",
            "form_rcdl": "form_rcdl",
            "form_rcdl:tf_reg_no": reg,
            "javax.faces.ViewState": viewstate
        }

        r2 = session.post("https://vahan.parivahan.gov.in/nrservices/faces/user/searchstatus.xhtml", data=payload, headers=headers)
        data_html = BeautifulSoup(r2.text, "html.parser").text

        if "Owner Name" not in data_html:
            await update.message.reply_text("❌ No data found or access blocked.")
            return

        fields = {
            "Owner Name": None,
            "Registration No": None,
            "Fuel Type": None,
            "Vehicle Class": None,
            "Model": None,
            "Registration Date": None,
            "Insurance Upto": None,
            "Fitness Upto": None
        }

        for key in fields:
            try:
                part = data_html.split(key + ":")[1].split("\n")[0].strip()
                fields[key] = part
            except:
                fields[key] = "N/A"

        result = f"""
🚘 Vehicle Plate: {reg}
👤 Owner: {fields['Owner Name']}
📅 Registered On: {fields['Registration Date']}
🛞 Vehicle Class: {fields['Vehicle Class']}
🛢️ Fuel Type: {fields['Fuel Type']}
🧰 Model: {fields['Model']}
🛡️ Insurance Till: {fields['Insurance Upto']}
💪 Fitness Till: {fields['Fitness Upto']}
✅ Source: Parivahan.gov.in
        """

    except Exception as e:
        result = f"⚠️ Error: {str(e)}"

    await update.message.reply_text(result)

# /ip <address>
async def ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /ip <IP Address>")
        return

    ip_address = context.args[0]
    await update.message.reply_text(f"🔍 Tracing IP: {ip_address}...")

    try:
        url = f"http://ip-api.com/json/{ip_address}"
        res = requests.get(url)
        data = res.json()

        if data['status'] != 'success':
            await update.message.reply_text("❌ Invalid IP address or no data found.")
            return

        result = f"""
🌐 IP Address: {ip_address}
🏙️ City: {data.get('city')}, {data.get('regionName')} ({data.get('country')})
📡 ISP: {data.get('isp')}
📍 Lat/Lon: {data.get('lat')}, {data.get('lon')}
🕵️‍♂️ VPN/Proxy: {data.get('proxy', 'Unknown')}
"""
    except Exception as e:
        result = f"⚠️ Error: {str(e)}"

    await update.message.reply_text(result)

# /username <name>
async def username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /username <name>")
        return

    uname = context.args[0]
    await update.message.reply_text(f"🔍 Searching platforms for username: {uname}...")

    try:
        sites = ["github.com", "instagram.com", "twitter.com", "tiktok.com", "reddit.com"]
        found = []
        for site in sites:
            url = f"https://{site}/{uname}"
            res = requests.get(url)
            if res.status_code == 200:
                found.append(url)

        if found:
            reply = "✅ Found on:\n" + "\n".join(found)
        else:
            reply = "❌ Username not found on checked platforms."
    except Exception as e:
        reply = f"⚠️ Error: {str(e)}"

    await update.message.reply_text(reply)

# /sim <phone>
async def sim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /sim +91xxxxxxxxxx")
        return

    number = context.args[0]
    await update.message.reply_text(f"🔍 Checking SIM info for {number}...")

    try:
        url = f"http://apilayer.net/api/validate?access_key={api_key}&number={number}&country_code=IN&format=1"
        res = requests.get(url)
        data = res.json()

        if not data['valid']:
            await update.message.reply_text("❌ Invalid number.")
            return

        reply = f"""
📞 Number: {data.get('international_format')}
📶 Carrier: {data.get('carrier', 'Unknown')}
📱 Line Type: {data.get('line_type', 'Unknown')}
🌍 Location: {data.get('location', 'Unknown')}
"""
    except Exception as e:
        reply = f"⚠️ Error: {str(e)}"

    await update.message.reply_text(reply)

# /address <query>
async def address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /address <full name> [optional: city/state]")
        return

    name = " ".join(context.args)
    await update.message.reply_text(f"🔍 Looking up address for: {name} (scraped)...")

    try:
        query = urllib.parse.quote_plus(f'{name} site:voters.eci.gov.in OR filetype:pdf address')
        url = f"https://www.google.com/search?q={query}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)

        links = re.findall(r'https://[^"\']+', response.text)
        matches = [l for l in links if any(x in l for x in ["eci.gov.in", ".pdf"])]

        if not matches:
            await update.message.reply_text("❌ No address info found from public sources.")
        else:
            reply = "✅ Top address-related hits:\n" + "\n".join(matches[:5])
            await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error during address search: {e}")

# /photo <query>
async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /photo <name/email/phone>")
        return

    query = " ".join(context.args)
    await update.message.reply_text(f"🖼️ Searching public image traces for: {query}...")

    try:
        with DDGS() as ddgs:
            results = ddgs.images(query, max_results=5)
            if not results:
                await update.message.reply_text("❌ No public images found.")
                return

            for img in results:
                await update.message.reply_photo(photo=img['image'])

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error during image search: {e}")

# Build app and add handlers
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("scan", scan))
app.add_handler(CommandHandler("plate", plate))
app.add_handler(CommandHandler("ip", ip))
app.add_handler(CommandHandler("username", username))
app.add_handler(CommandHandler("sim", sim))
app.add_handler(CommandHandler("address", address))
app.add_handler(CommandHandler("photo", photo))

print("✅ Bot is running. Waiting for commands...")
app.run_polling()
