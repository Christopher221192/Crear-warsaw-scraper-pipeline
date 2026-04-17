import json
import logging
import os
import shutil

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def calculate_score(item):
    """
    Base Score: 50
    + up to 20 for proximity to metro (closer is better, max points if < 300m)
    + up to 15 for market difference (undervalued = points)
    + up to 10 for capital gain percentage
    + 5 for optimal layout
    """
    score = 50.0
    
    # 1. Metro distance (0-20 points)
    # Scale: < 300m = 20 pts, > 2000m = 0 pts
    dist = item.get("walking_distance_m", 2000)
    if dist < 300:
        score += 20
    elif dist > 2000:
        score += 0
    else:
        # Linear scale inversely proportional
        score += max(0, 20 * (1 - ((dist - 300) / 1700)))
        
    # 2. Market Diff (-20 to +15 points based on % vs NBP)
    # market_diff string format: "+21.26%" or "-5.00%"
    md_str = item.get("market_diff", "0%")
    try:
        if md_str == "N/A":
            md_val = 0
        else:
            md_val = float(md_str.replace("%", "").replace("+", ""))
            
        # If it's cheaper than average (md_val < 0), ADD points.
        # e.g., -20% vs district avg => 15 points
        if md_val <= -20:
            score += 15
        elif md_val >= 20:
            score -= 10
        else:
            # Scale
            score += -1 * (md_val / 20) * 15 # Wait, if md is -10 (cheaper), -1 * (-0.5) * 15 = 7.5 pts
    except:
        pass
        
    # 3. Capital Gain (0-10)
    # Expected e.g. 25-35%. Let's say > 30% gets 10 points.
    inv = item.get("investment_analysis", {})
    cap_gain = inv.get("projection_2031", {}).get("expected_capital_gain_pct", 0)
    if cap_gain >= 30:
        score += 10
    else:
        score += (max(cap_gain, 0) / 30.0) * 10
        
    # 4. Layout
    layout = inv.get("vision_ai_layout", "")
    if "Óptima" in layout:
        score += 5
    elif "Subóptima" in layout:
        score -= 5
        
    return min(100, max(0, round(score)))

def process():
    in_file = "warsaw_apartments_2027_investment.json"
    out_file = "warsaw_apartments_scored.json"
    nextjs_dest = "../ProyectoPolandHouse/public/data/apartments.json"
    
    if not os.path.exists(in_file):
        logging.error("Source file missing.")
        return
        
    with open(in_file, "r") as f:
        data = json.load(f)
        
    for item in data:
        item["opportunity_score"] = calculate_score(item)
        # Adding a fake id if doesn't exist
        if not item.get("id"):
            item["id"] = str(hash(item.get("title")))
        
    # Sort by score descending (top ranking)
    data = sorted(data, key=lambda x: x.get("opportunity_score", 0), reverse=True)
    
    with open(out_file, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
    # Export to Frontend (Optional if sibling exists)
    try:
        os.makedirs(os.path.dirname(nextjs_dest), exist_ok=True)
        shutil.copyfile(out_file, nextjs_dest)
        logging.info(f"Processed {len(data)} items and exported to Frontend {nextjs_dest}")
    except Exception as e:
        logging.warning(f"Could not export to frontend: {e}. This is normal in CI/CD if folders are detached.")

if __name__ == "__main__":
    process()
