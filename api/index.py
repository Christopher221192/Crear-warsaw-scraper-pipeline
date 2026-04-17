import os
import requests
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

# Configuration from Environment Variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_CHAT_ID = os.getenv("ALLOWED_CHAT_ID")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO_OWNER = os.getenv("GITHUB_REPO_OWNER")
GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME", "Crear-warsaw-scraper-pipeline")
GITHUB_WORKFLOW_NAME = "scraper.yml"

@app.post("/api/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    
    if "message" not in data:
        return {"status": "ignored", "reason": "no message in data"}
    
    message = data["message"]
    chat_id = str(message.get("chat", {}).get("id"))
    text = message.get("text", "")
    
    # 1. Security Check: Only allow from specified User/Chat
    if ALLOWED_CHAT_ID and chat_id != str(ALLOWED_CHAT_ID):
        print(f"Unauthorized chat_id: {chat_id}")
        return {"status": "unauthorized"}

    # 2. Command Check
    if text.strip().lower() == "/run":
        # 3. Trigger GitHub Action
        github_url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/actions/workflows/{GITHUB_WORKFLOW_NAME}/dispatches"
        
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        payload = {
            "ref": "main"  # Adjust if your default branch is different
        }
        
        response = requests.post(github_url, headers=headers, json=payload)
        
        if response.status_code == 204:
            send_telegram_status(chat_id, "🚀 ¡Scraper activado correctamente en GitHub Actions!")
            return {"status": "success", "action": "triggered"}
        else:
            error_msg = f"Error triggering GitHub: {response.status_code} - {response.text}"
            send_telegram_status(chat_id, f"❌ Error al activar el scraper: {response.status_code}")
            return {"status": "error", "details": error_msg}
            
    return {"status": "ignored", "command": text}

def send_telegram_status(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

@app.get("/")
async def health():
    return {"status": "ok", "service": "poland-house-telegram-bridge"}
