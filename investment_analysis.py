import json
import logging
import random
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def simulate_vision_ai():
    """
    Mock function to simulate a Vision AI evaluation on the apartment layout.
    Checks if distribution is 'Óptima', 'Aceptable', or 'Mala'.
    """
    verdicts = ["Óptima (Poco pasillo, buena iluminación)", "Aceptable", "Subóptima (Mucho pasillo, espacios ciegos)"]
    weights = [0.4, 0.4, 0.2]
    return random.choices(verdicts, weights)[0]

def calc_mortgage_payment(principal, annual_rate, years):
    """
    Calculate fixed monthly mortgage payment.
    """
    monthly_rate = annual_rate / 12 / 100
    num_payments = years * 12
    if monthly_rate == 0:
        return principal / num_payments
    return principal * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)

def calc_rent_yield(price_per_m2, total_m2, district, nearest_metro_m):
    """
    Calculate an estimated Monthly Rent in PLN using a hybrid yield and m2 dynamic model
    For Warsaw 2026, avg rent is ~65-80 PLN/m2.
    Premium applied if < 500m to Metro.
    """
    base_rent_per_m2 = 70  # Baseline PLN per m2
    
    # Premium by district quality (proxy)
    if any(q in district for q in ["Śródmieście", "Mokotów", "Wola"]):
        base_rent_per_m2 += 15
    elif any(q in district for q in ["Żoliborz", "Ochota", "Wilanów"]):
        base_rent_per_m2 += 10
        
    # Premium by metro distance
    if nearest_metro_m is not None and nearest_metro_m < 500:
        base_rent_per_m2 += 5
        
    monthly_rent = base_rent_per_m2 * total_m2
    # Cap to a standard gross yield logic (don't let it be extremely unrealistic over 9%)
    max_reasonable_rent = (total_m2 * price_per_m2) * 0.08 / 12
    return min(monthly_rent, max_reasonable_rent)

def process_investment():
    logging.info("Loading Stage 2 enriched data...")
    with open("warsaw_apartments_2027_enriched.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    investment_data = []
    
    # Mortgage parameters
    down_payment_pct = 0.20
    wibor_3m = 3.85
    bank_margin = 2.00
    annual_interest_rate = wibor_3m + bank_margin
    mortgage_years = 30
    
    for idx, item in enumerate(data):
        price = item.get("total_price")
        price_m2 = item.get("price_per_m2")
        
        if not price or not price_m2:
            item["investment_analysis"] = {"error": "Missing price data"}
            investment_data.append(item)
            continue
            
        total_m2 = price / price_m2
        
        # 1. Vision AI Placeholder
        layout_quality = simulate_vision_ai()
        if "Mieszkanie 1-pokojowe" in item.get("title", "") and "Óptima" in layout_quality:
            layout_quality = "Aceptable" # Hard to have an "optimal" 1-bedroom with no hallway waste
            
        # 2. Mortgage Simulator
        down_payment = price * down_payment_pct
        loan_amount = price - down_payment
        monthly_mortgage_payment = calc_mortgage_payment(loan_amount, annual_interest_rate, mortgage_years)
        
        # 3. Rent Estimator and Break-Even
        dist_m = item.get("walking_distance_m", 1000)
        monthly_rent = calc_rent_yield(price_m2, total_m2, item.get("district", ""), dist_m)
        annual_rent = monthly_rent * 12
        gross_yield = (annual_rent / price) * 100
        
        monthly_cashflow = monthly_rent - monthly_mortgage_payment
        
        # Break-Even: Year when accumulated rent covers 100% of the property total price
        break_even_years = round(price / annual_rent, 1) if annual_rent > 0 else 999
        
        # 4. 2031 Price Projection
        # 3% annual compound over 5 years = Base * (1.03^5)
        # EU 2026 Energy Efficiency Premium = +10%
        fv_factor_5y = (1.03 ** 5)
        premium = 1.10
        projected_price_2031 = price * fv_factor_5y * premium
        capital_gain = projected_price_2031 - price
        
        analysis = {
            "vision_ai_layout": layout_quality,
            "mortgage_sim": {
                "interest_rate_pct": annual_interest_rate,
                "down_payment": round(down_payment, 2),
                "loan_amount": round(loan_amount, 2),
                "monthly_payment_pln": round(monthly_mortgage_payment, 2)
            },
            "rent_sim": {
                "estimated_monthly_rent_pln": round(monthly_rent, 2),
                "gross_yield_pct": round(gross_yield, 2),
                "monthly_cashflow_pln": round(monthly_cashflow, 2),
                "break_even_years_from_rent": break_even_years
            },
            "projection_2031": {
                "estimated_value_pln": round(projected_price_2031, 2),
                "expected_capital_gain_pln": round(capital_gain, 2),
                "expected_capital_gain_pct": round((capital_gain / price) * 100, 2)
            }
        }
        
        item["investment_analysis"] = analysis
        investment_data.append(item)
        
    with open("warsaw_apartments_2027_investment.json", "w", encoding="utf-8") as f:
        json.dump(investment_data, f, indent=4, ensure_ascii=False)
        
    logging.info(f"Investment Analysis completed for {len(data)} items!")
    
if __name__ == "__main__":
    process_investment()
