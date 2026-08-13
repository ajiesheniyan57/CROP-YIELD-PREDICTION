import os
import joblib
import numpy as np

# Load trained models and encoders safely
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "crop_yield_model.pkl")
AREA_ENCODER_PATH = os.path.join(BASE_DIR, "area_encoder.pkl")
ITEM_ENCODER_PATH = os.path.join(BASE_DIR, "item_encoder (2).pkl")

model = joblib.load(MODEL_PATH)
area_encoder = joblib.load(AREA_ENCODER_PATH)
item_encoder = joblib.load(ITEM_ENCODER_PATH)

# List of available options
AVAILABLE_AREAS = sorted(list(area_encoder.classes_))
AVAILABLE_CROPS = sorted(list(item_encoder.classes_))

SOIL_TYPES = ["Alluvial", "Black", "Clay", "Loamy", "Red", "Sandy", "Silt"]
WATER_AVAILABILITY_OPTIONS = [
    "Low (Rainfed)",
    "Moderate (Seasonal Irrigation)",
    "High (Canal / Drip Irrigation)"
]
WATER_QUALITY_OPTIONS = [
    "Optimal Freshwater (pH 6.5 - 7.5)",
    "Slight Salinity / Mineralized",
    "High Salinity / Brackish",
    "Acidic Water (pH < 6.0)",
    "Alkaline Water (pH > 8.0)"
]
SEASONS = ["Kharif (Monsoon)", "Rabi (Winter)", "Zaid (Summer)", "Autumn", "Whole Year"]

# Agronomic Compatibility Matrices
SOIL_SUITABILITY = {
    "Rice, paddy": {"Clay": 1.15, "Alluvial": 1.10, "Silt": 1.05, "Loamy": 0.95, "Black": 0.90, "Red": 0.80, "Sandy": 0.65},
    "Wheat": {"Loamy": 1.15, "Alluvial": 1.12, "Black": 1.05, "Silt": 1.00, "Clay": 0.88, "Red": 0.82, "Sandy": 0.70},
    "Maize": {"Loamy": 1.15, "Alluvial": 1.10, "Black": 1.08, "Red": 0.95, "Silt": 0.92, "Clay": 0.85, "Sandy": 0.75},
    "Potatoes": {"Sandy": 1.15, "Loamy": 1.12, "Alluvial": 1.08, "Silt": 0.95, "Red": 0.90, "Black": 0.75, "Clay": 0.60},
    "Cassava": {"Sandy": 1.12, "Loamy": 1.10, "Red": 1.05, "Alluvial": 1.00, "Black": 0.90, "Silt": 0.85, "Clay": 0.75},
    "Soybeans": {"Loamy": 1.15, "Black": 1.12, "Alluvial": 1.08, "Silt": 0.95, "Red": 0.90, "Clay": 0.85, "Sandy": 0.70},
    "Sorghum": {"Black": 1.15, "Loamy": 1.10, "Alluvial": 1.05, "Red": 1.00, "Sandy": 0.90, "Silt": 0.88, "Clay": 0.80},
    "Sweet potatoes": {"Sandy": 1.15, "Loamy": 1.12, "Alluvial": 1.05, "Red": 0.95, "Silt": 0.90, "Black": 0.85, "Clay": 0.70},
    "Yams": {"Loamy": 1.15, "Alluvial": 1.10, "Silt": 1.05, "Red": 0.95, "Black": 0.90, "Sandy": 0.80, "Clay": 0.70},
    "Plantains and others": {"Alluvial": 1.15, "Loamy": 1.12, "Silt": 1.05, "Clay": 0.95, "Black": 0.90, "Red": 0.85, "Sandy": 0.70}
}

WATER_AVAIL_FACTORS = {
    "Low (Rainfed)": 0.82,
    "Moderate (Seasonal Irrigation)": 1.00,
    "High (Canal / Drip Irrigation)": 1.15
}

WATER_QUALITY_FACTORS = {
    "Optimal Freshwater (pH 6.5 - 7.5)": 1.00,
    "Slight Salinity / Mineralized": 0.88,
    "High Salinity / Brackish": 0.65,
    "Acidic Water (pH < 6.0)": 0.82,
    "Alkaline Water (pH > 8.0)": 0.84
}

SEASON_SUITABILITY = {
    "Rice, paddy": {"Kharif (Monsoon)": 1.15, "Zaid (Summer)": 1.05, "Autumn": 1.00, "Whole Year": 1.00, "Rabi (Winter)": 0.80},
    "Wheat": {"Rabi (Winter)": 1.20, "Autumn": 1.05, "Whole Year": 1.00, "Kharif (Monsoon)": 0.70, "Zaid (Summer)": 0.60},
    "Maize": {"Kharif (Monsoon)": 1.10, "Zaid (Summer)": 1.08, "Whole Year": 1.00, "Rabi (Winter)": 0.95, "Autumn": 0.90},
    "Potatoes": {"Rabi (Winter)": 1.18, "Autumn": 1.05, "Whole Year": 1.00, "Zaid (Summer)": 0.75, "Kharif (Monsoon)": 0.70},
    "Cassava": {"Whole Year": 1.10, "Kharif (Monsoon)": 1.05, "Autumn": 1.00, "Zaid (Summer)": 0.95, "Rabi (Winter)": 0.90},
    "Soybeans": {"Kharif (Monsoon)": 1.15, "Autumn": 1.02, "Whole Year": 1.00, "Zaid (Summer)": 0.85, "Rabi (Winter)": 0.75},
    "Sorghum": {"Kharif (Monsoon)": 1.12, "Zaid (Summer)": 1.08, "Whole Year": 1.00, "Rabi (Winter)": 0.90, "Autumn": 0.88},
    "Sweet potatoes": {"Kharif (Monsoon)": 1.10, "Whole Year": 1.05, "Autumn": 1.00, "Zaid (Summer)": 0.90, "Rabi (Winter)": 0.85},
    "Yams": {"Kharif (Monsoon)": 1.12, "Whole Year": 1.05, "Autumn": 1.00, "Zaid (Summer)": 0.88, "Rabi (Winter)": 0.80},
    "Plantains and others": {"Whole Year": 1.15, "Kharif (Monsoon)": 1.08, "Autumn": 1.00, "Zaid (Summer)": 0.95, "Rabi (Winter)": 0.90}
}

# Default Market Prices ($ per Tonne) & Base Costs ($ per Hectare)
CROP_FINANCIAL_DEFAULTS = {
    "Rice, paddy": {"market_price": 380.0, "seed_cost": 120.0, "base_fertilizer": 140.0},
    "Wheat": {"market_price": 320.0, "seed_cost": 100.0, "base_fertilizer": 130.0},
    "Maize": {"market_price": 260.0, "seed_cost": 90.0, "base_fertilizer": 125.0},
    "Potatoes": {"market_price": 450.0, "seed_cost": 250.0, "base_fertilizer": 180.0},
    "Cassava": {"market_price": 210.0, "seed_cost": 75.0, "base_fertilizer": 90.0},
    "Soybeans": {"market_price": 520.0, "seed_cost": 135.0, "base_fertilizer": 110.0},
    "Sorghum": {"market_price": 240.0, "seed_cost": 65.0, "base_fertilizer": 85.0},
    "Sweet potatoes": {"market_price": 410.0, "seed_cost": 160.0, "base_fertilizer": 140.0},
    "Yams": {"market_price": 480.0, "seed_cost": 210.0, "base_fertilizer": 150.0},
    "Plantains and others": {"market_price": 600.0, "seed_cost": 300.0, "base_fertilizer": 160.0}
}

def predict_crop_yield_and_finance(
    area_name: str,
    item_name: str,
    year: float,
    rainfall: float,
    pesticides: float,
    temp: float,
    soil_type: str,
    water_availability: str,
    water_quality: str,
    season: str,
    farm_area: float = 10.0,
    custom_market_price: float = None
):
    """
    Computes predicted crop yield in Tonnes and calculates full spending, revenue, and profit.
    """
    # 1. Encode Area and Item for pre-trained Random Forest model
    encoded_area = area_encoder.transform([area_name])[0]
    encoded_item = item_encoder.transform([item_name])[0]

    # Pre-trained model expects [area, item, year, rainfall, pesticides, temp]
    input_features = np.array([[
        encoded_area,
        encoded_item,
        float(year),
        float(rainfall),
        float(pesticides),
        float(temp)
    ]])

    # Base yield predicted in hg/ha (hectograms per hectare)
    raw_base_yield_hg_ha = float(model.predict(input_features)[0])
    
    # Standard conversion: 10,000 hg/ha = 1 Tonne / hectare
    base_yield_tonnes_ha = max(0.1, raw_base_yield_hg_ha / 10000.0)

    # 2. Compute Agronomic Suitability Factors
    crop_soil_map = SOIL_SUITABILITY.get(item_name, {})
    soil_factor = crop_soil_map.get(soil_type, 1.00)

    water_avail_factor = WATER_AVAIL_FACTORS.get(water_availability, 1.00)
    water_qual_factor = WATER_QUALITY_FACTORS.get(water_quality, 1.00)

    crop_season_map = SEASON_SUITABILITY.get(item_name, {})
    season_factor = crop_season_map.get(season, 1.00)

    # Climate suitability factor fine-tuning
    climate_factor = 1.0
    if temp < 10 or temp > 40:
        climate_factor *= 0.85
    elif 20 <= temp <= 32:
        climate_factor *= 1.05

    if rainfall < 300:
        climate_factor *= 0.80
    elif 800 <= rainfall <= 2000:
        climate_factor *= 1.05

    # Net Yield per Hectare (Tonnes / Ha)
    final_yield_tonnes_ha = base_yield_tonnes_ha * soil_factor * water_avail_factor * water_qual_factor * season_factor * climate_factor

    # Total Yield for Farm Size (Tonnes)
    total_yield_tonnes = final_yield_tonnes_ha * float(farm_area)

    # 3. Compute Spending Breakdown ($)
    crop_defaults = CROP_FINANCIAL_DEFAULTS.get(item_name, {"market_price": 350.0, "seed_cost": 100.0, "base_fertilizer": 120.0})

    seed_cost_ha = crop_defaults["seed_cost"]
    
    pesticide_cost_ha = max(30.0, (float(pesticides) / max(1.0, float(rainfall))) * 25.0 + 40.0)

    water_cost_map = {
        "Low (Rainfed)": 35.0,
        "Moderate (Seasonal Irrigation)": 110.0,
        "High (Canal / Drip Irrigation)": 220.0
    }
    water_cost_ha = water_cost_map.get(water_availability, 100.0)

    if "Salinity" in water_quality or "Acidic" in water_quality or "Alkaline" in water_quality:
        water_cost_ha += 45.0

    soil_treatment_map = {"Sandy": 160.0, "Clay": 130.0, "Red": 145.0, "Black": 110.0, "Alluvial": 95.0, "Loamy": 90.0, "Silt": 105.0}
    fertilizer_cost_ha = crop_defaults["base_fertilizer"] + soil_treatment_map.get(soil_type, 110.0)

    labor_machinery_cost_ha = 220.0 + (final_yield_tonnes_ha * 12.0)

    spending_per_ha = seed_cost_ha + pesticide_cost_ha + water_cost_ha + fertilizer_cost_ha + labor_machinery_cost_ha
    total_spending = spending_per_ha * float(farm_area)

    # 4. Revenue and Net Profit Calculation
    try:
        parsed_price = float(custom_market_price) if custom_market_price is not None and str(custom_market_price).strip() != "" else None
    except (ValueError, TypeError):
        parsed_price = None
    market_price = parsed_price if (parsed_price is not None and parsed_price > 0) else crop_defaults["market_price"]
    
    gross_revenue = total_yield_tonnes * market_price
    net_profit = gross_revenue - total_spending

    roi_percent = (net_profit / total_spending * 100.0) if total_spending > 0 else 0.0
    profit_margin_percent = (net_profit / gross_revenue * 100.0) if gross_revenue > 0 else 0.0
    breakeven_price = total_spending / total_yield_tonnes if total_yield_tonnes > 0 else 0.0

    agronomic_score = int(min(100, max(20, round(
        (soil_factor * 0.25 + water_avail_factor * 0.25 + water_qual_factor * 0.25 + season_factor * 0.25) * 85
    ))))

    return {
        "area": area_name,
        "crop": item_name,
        "year": int(year),
        "farm_area_ha": round(float(farm_area), 2),
        "yield_per_ha_tonnes": round(final_yield_tonnes_ha, 3),
        "total_yield_tonnes": round(total_yield_tonnes, 2),
        "raw_ml_base_yield_hg_ha": round(raw_base_yield_hg_ha, 2),
        "agronomic_score": agronomic_score,
        "spending_breakdown_per_ha": {
            "Seeds & Planting": round(seed_cost_ha, 2),
            "Pesticides & Protection": round(pesticide_cost_ha, 2),
            "Water & Irrigation": round(water_cost_ha, 2),
            "Fertilizers & Soil": round(fertilizer_cost_ha, 2),
            "Labor & Machinery": round(labor_machinery_cost_ha, 2)
        },
        "spending_breakdown_total": {
            "Seeds & Planting": round(seed_cost_ha * float(farm_area), 2),
            "Pesticides & Protection": round(pesticide_cost_ha * float(farm_area), 2),
            "Water & Irrigation": round(water_cost_ha * float(farm_area), 2),
            "Fertilizers & Soil": round(fertilizer_cost_ha * float(farm_area), 2),
            "Labor & Machinery": round(labor_machinery_cost_ha * float(farm_area), 2)
        },
        "spending_per_ha": round(spending_per_ha, 2),
        "total_spending": round(total_spending, 2),
        "market_price_per_tonne": round(market_price, 2),
        "gross_revenue": round(gross_revenue, 2),
        "net_profit": round(net_profit, 2),
        "roi_percent": round(roi_percent, 1),
        "profit_margin_percent": round(profit_margin_percent, 1),
        "breakeven_price": round(breakeven_price, 2),
        "factors": {
            "soil_factor": round(soil_factor, 2),
            "water_avail_factor": round(water_avail_factor, 2),
            "water_qual_factor": round(water_qual_factor, 2),
            "season_factor": round(season_factor, 2),
            "climate_factor": round(climate_factor, 2)
        }
    }


def get_weather_data(area_name: str):
    """
    Returns regional weather metrics, agro-climatic conditions, and yield risk warnings.
    """
    # Hash or lookup regional agro-climatic profile
    base_hash = sum(ord(c) for c in area_name) if area_name else 100
    
    # Regional defaults for key FAO agricultural zones
    climate_profiles = {
        "India": {"temp": 26.5, "rainfall": 1150.0, "humidity": 72, "solar_rad": 19.5, "zone": "Tropical / Subtropical Monsoon"},
        "United States of America": {"temp": 16.0, "rainfall": 850.0, "humidity": 62, "solar_rad": 17.0, "zone": "Temperate / Continental"},
        "Brazil": {"temp": 24.8, "rainfall": 1600.0, "humidity": 78, "solar_rad": 21.0, "zone": "Tropical Rainforest & Savannah"},
        "China": {"temp": 18.2, "rainfall": 920.0, "humidity": 65, "solar_rad": 16.5, "zone": "Temperate & Monsoon"},
        "Spain": {"temp": 19.5, "rainfall": 580.0, "humidity": 55, "solar_rad": 20.0, "zone": "Mediterranean Arid / Semi-Arid"},
        "Nigeria": {"temp": 28.0, "rainfall": 1350.0, "humidity": 75, "solar_rad": 22.0, "zone": "Tropical West Africa"},
        "Australia": {"temp": 22.0, "rainfall": 480.0, "humidity": 50, "solar_rad": 23.5, "zone": "Arid / Semi-Arid"}
    }

    if area_name in climate_profiles:
        profile = climate_profiles[area_name]
    else:
        # Algorithmic deterministic generator for all other FAO countries
        temp = round(14.0 + (base_hash % 180) / 10.0, 1)
        rainfall = round(350.0 + (base_hash * 7) % 1500, 1)
        humidity = int(45 + (base_hash % 40))
        solar_rad = round(14.0 + (base_hash % 90) / 10.0, 1)
        profile = {
            "temp": temp,
            "rainfall": rainfall,
            "humidity": humidity,
            "solar_rad": solar_rad,
            "zone": "Global FAO Agricultural Zone"
        }

    # Evaluate Agro-Climatic Risks
    risks = []
    if profile["rainfall"] < 400:
        risks.append({"level": "HIGH", "type": "Drought Risk", "message": "Low precipitation detected. Drip/Canal irrigation recommended."})
    elif profile["rainfall"] > 1800:
        risks.append({"level": "MEDIUM", "type": "Flood / Waterlogging Risk", "message": "High rainfall. Ensure adequate field drainage to avoid root rot."})

    if profile["temp"] > 32:
        risks.append({"level": "HIGH", "type": "Heat Stress Warning", "message": "Extreme temperatures may reduce grain filling."})
    elif profile["temp"] < 12:
        risks.append({"level": "MEDIUM", "type": "Frost / Cold Stress", "message": "Low temperatures may delay vegetative growth."})

    if not risks:
        risks.append({"level": "LOW", "type": "Optimal Conditions", "message": "Agro-climatic indicators are within ideal ranges for cultivation."})

    return {
        "area": area_name,
        "temperature_celsius": profile["temp"],
        "annual_rainfall_mm": profile["rainfall"],
        "relative_humidity_percent": profile["humidity"],
        "solar_radiation_mj_m2": profile["solar_rad"],
        "agro_climatic_zone": profile["zone"],
        "risk_alerts": risks
    }


def compare_scenarios(scenario_list: list):
    """
    Compares multiple scenario parameter dictionaries or saved scenario objects side-by-side.
    Identifies top ROI, top yield, lowest spending, and calculates comparative deltas.
    """
    if not scenario_list:
        return {"status": "error", "message": "No scenarios provided for comparison"}

    processed_results = []
    for index, item in enumerate(scenario_list):
        if isinstance(item, dict) and "total_yield_tonnes" in item and "net_profit" in item:
            # Already calculated scenario dict
            res = item
            scenario_name = item.get("scenario_name", f"Scenario {index + 1}")
        else:
            # Input parameter payload to predict
            s_name = item.get("scenario_name", f"Option {index + 1}")
            area = item.get("area", "India")
            crop = item.get("crop", "Wheat")
            year = item.get("year", 2024)
            rainfall = float(item.get("rainfall", 1000))
            pesticides = float(item.get("pesticides", 150))
            temp = float(item.get("temp", 25))
            soil_type = item.get("soil_type", "Loamy")
            water_avail = item.get("water_availability", "Moderate (Seasonal Irrigation)")
            water_qual = item.get("water_quality", "Optimal Freshwater (pH 6.5 - 7.5)")
            season = item.get("season", "Kharif (Monsoon)")
            farm_area = float(item.get("farm_area", 10.0))
            raw_mp = item.get("market_price")
            try:
                market_price = float(raw_mp) if raw_mp is not None and str(raw_mp).strip() != "" else None
            except (ValueError, TypeError):
                market_price = None

            res = predict_crop_yield_and_finance(
                area_name=area, item_name=crop, year=year, rainfall=rainfall,
                pesticides=pesticides, temp=temp, soil_type=soil_type,
                water_availability=water_avail, water_quality=water_qual,
                season=season, farm_area=farm_area, custom_market_price=market_price
            )
            scenario_name = s_name

        res_copy = dict(res)
        res_copy["scenario_name"] = scenario_name
        processed_results.append(res_copy)

    # Sort & Rank Scenarios
    best_roi_scenario = max(processed_results, key=lambda s: s.get("roi_percent", 0))
    best_yield_scenario = max(processed_results, key=lambda s: s.get("total_yield_tonnes", 0))
    best_profit_scenario = max(processed_results, key=lambda s: s.get("net_profit", 0))
    lowest_cost_scenario = min(processed_results, key=lambda s: s.get("total_spending", float('inf')))

    return {
        "compared_scenarios_count": len(processed_results),
        "scenarios": processed_results,
        "summary_highlights": {
            "top_roi": {
                "scenario_name": best_roi_scenario.get("scenario_name"),
                "crop": best_roi_scenario.get("crop"),
                "roi_percent": best_roi_scenario.get("roi_percent")
            },
            "highest_net_profit": {
                "scenario_name": best_profit_scenario.get("scenario_name"),
                "crop": best_profit_scenario.get("crop"),
                "net_profit": best_profit_scenario.get("net_profit")
            },
            "highest_total_yield": {
                "scenario_name": best_yield_scenario.get("scenario_name"),
                "crop": best_yield_scenario.get("crop"),
                "total_yield_tonnes": best_yield_scenario.get("total_yield_tonnes")
            },
            "lowest_input_cost": {
                "scenario_name": lowest_cost_scenario.get("scenario_name"),
                "crop": lowest_cost_scenario.get("crop"),
                "total_spending": lowest_cost_scenario.get("total_spending")
            }
        }
    }


def optimize_crop_portfolio(
    total_farm_area: float,
    budget: float,
    soil_type: str,
    area_name: str,
    candidate_crops: list = None
):
    """
    Computes an optimal land allocation strategy across candidate crops to maximize net farm return.
    """
    if not candidate_crops or len(candidate_crops) == 0:
        candidate_crops = ["Wheat", "Rice, paddy", "Maize", "Potatoes", "Soybeans"]

    weather = get_weather_data(area_name)
    crop_evaluations = []

    for crop in candidate_crops:
        if crop not in AVAILABLE_CROPS:
            continue
        
        # Simulate 1 Hectare prediction
        res = predict_crop_yield_and_finance(
            area_name=area_name,
            item_name=crop,
            year=2024,
            rainfall=weather["annual_rainfall_mm"],
            pesticides=150,
            temp=weather["temperature_celsius"],
            soil_type=soil_type,
            water_availability="Moderate (Seasonal Irrigation)",
            water_quality="Optimal Freshwater (pH 6.5 - 7.5)",
            season="Kharif (Monsoon)",
            farm_area=1.0
        )
        
        crop_evaluations.append({
            "crop": crop,
            "profit_per_ha": res["net_profit"],
            "cost_per_ha": res["spending_per_ha"],
            "yield_per_ha": res["yield_per_ha_tonnes"],
            "roi_percent": res["roi_percent"],
            "agronomic_score": res["agronomic_score"]
        })

    if not crop_evaluations:
        return {"status": "error", "message": "No valid candidate crops found"}

    # Sort crops by Net Profit per Hectare
    crop_evaluations.sort(key=lambda c: c["profit_per_ha"], reverse=True)

    # Allocate land based on budget & diversification rule (max 50% land to top crop)
    allocations = []
    remaining_area = float(total_farm_area)
    remaining_budget = float(budget) if budget and float(budget) > 0 else float('inf')

    num_crops = min(len(crop_evaluations), 3)
    top_crops = crop_evaluations[:num_crops]

    # Target weight split: 50%, 30%, 20%
    weights = [0.50, 0.30, 0.20] if num_crops == 3 else ([0.60, 0.40] if num_crops == 2 else [1.00])

    total_allocated_area = 0.0
    total_projected_profit = 0.0
    total_projected_spending = 0.0
    total_projected_yield = 0.0

    for idx, c_info in enumerate(top_crops):
        target_ha = round(total_farm_area * weights[idx], 2)
        # Check budget constraint
        required_spending = target_ha * c_info["cost_per_ha"]
        
        if remaining_budget < float('inf') and required_spending > remaining_budget:
            # Adjust area to budget limit
            target_ha = round(max(0.0, remaining_budget / c_info["cost_per_ha"]), 2)
            required_spending = target_ha * c_info["cost_per_ha"]

        if target_ha <= 0:
            continue

        allocated_profit = target_ha * c_info["profit_per_ha"]
        allocated_yield = target_ha * c_info["yield_per_ha"]

        allocations.append({
            "crop": c_info["crop"],
            "allocated_area_ha": target_ha,
            "allocated_area_percent": round((target_ha / max(0.001, total_farm_area)) * 100, 1),
            "projected_cost": round(required_spending, 2),
            "projected_profit": round(allocated_profit, 2),
            "projected_yield_tonnes": round(allocated_yield, 2),
            "agronomic_score": c_info["agronomic_score"]
        })

        total_allocated_area += target_ha
        total_projected_profit += allocated_profit
        total_projected_spending += required_spending
        total_projected_yield += allocated_yield
        remaining_budget -= required_spending

    return {
        "status": "success",
        "total_farm_area_ha": total_farm_area,
        "total_allocated_area_ha": round(total_allocated_area, 2),
        "total_projected_spending": round(total_projected_spending, 2),
        "total_projected_profit": round(total_projected_profit, 2),
        "total_projected_yield_tonnes": round(total_projected_yield, 2),
        "portfolio_roi_percent": round((total_projected_profit / total_projected_spending * 100), 1) if total_projected_spending > 0 else 0.0,
        "allocations": allocations
    }

