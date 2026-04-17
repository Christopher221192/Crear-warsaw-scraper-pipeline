import json
import logging
import os
import time

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] ALERT SYSTEM - %(message)s')

HISTORY_DB = "price_history_db.json"
INPUT_FILE = "warsaw_apartments_scored.json"

def run_watcher():
    if not os.path.exists(INPUT_FILE):
        return
        
    with open(INPUT_FILE, "r") as f:
        current_data = json.load(f)
        
    history = {}
    if os.path.exists(HISTORY_DB):
        with open(HISTORY_DB, "r") as f:
            history = json.load(f)
            
    alerts_triggered = 0
            
    for item in current_data:
        prop_id = str(item.get("id"))
        current_price = item.get("total_price")
        
        if not current_price:
            continue
            
        if prop_id in history:
            old_price = history[prop_id].get("last_price")
            # Has price dropped by 5%?
            threshold = old_price * 0.95
            if current_price <= threshold:
                logging.info(f"PRICE DROP DETECTED on item {prop_id}! Old: {old_price}, New: {current_price}")
                # Boost Score algorithmically
                item["opportunity_score"] = min(100, item.get("opportunity_score", 0) + 15)
                history[prop_id]["last_price"] = current_price
                
                if item["opportunity_score"] >= 90:
                    logging.warning(f"*** PUSH NOTIFICATION: High Opportunity Property! Score: {item['opportunity_score']} | Title: {item.get('title')}")
                    alerts_triggered += 1
        else:
            # First time seeing this property
            history[prop_id] = {"last_price": current_price}
            
    with open(HISTORY_DB, "w") as f:
        json.dump(history, f, indent=4)
        
    # Overwrite the feed optionally if we want the boosted scores reflected in UI immediately
    if alerts_triggered > 0:
        with open(INPUT_FILE, "w") as f:
            json.dump(current_data, f, indent=4)
        
        # update frontend copy if needed
        import shutil
        nextjs_dest = "../ProyectoPolandHouse/public/data/apartments.json"
        if os.path.exists(os.path.dirname(nextjs_dest)):
            shutil.copyfile(INPUT_FILE, nextjs_dest)

if __name__ == "__main__":
    logging.info("Starting Price Watcher daemon (simulated run)")
    run_watcher()
    logging.info("Run finished. Scheduled next run in 6 hours.")
