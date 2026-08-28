import csv
import io
import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, make_response, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flasgger import Swagger

import yield_engine as ye
import model_monitoring as mm
from models import db, User, SavedScenario

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Persistent secret key for continuous session validity across restarts
SECRET_KEY_FILE = os.path.join(BASE_DIR, '.secret_key')
if os.environ.get('SECRET_KEY'):
    secret_key = os.environ.get('SECRET_KEY')
elif os.path.exists(SECRET_KEY_FILE):
    with open(SECRET_KEY_FILE, 'r') as f:
        secret_key = f.read().strip()
else:
    import secrets
    secret_key = secrets.token_hex(32)
    try:
        with open(SECRET_KEY_FILE, 'w') as f:
            f.write(secret_key)
    except Exception:
        pass

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, 'agriyield.db')}")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'
app.config['REMEMBER_COOKIE_REFRESH_EACH_REQUEST'] = True

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'home'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


with app.app_context():
    db.create_all()

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs/"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "AgriYield AI Intelligence Engine API",
        "description": "RESTful API for Machine Learning Crop Yield Prediction, Database Persistence & User Authentication",
        "contact": {
            "name": "AgriYield AI Team"
        },
        "version": "2.0.0"
    },
    "basePath": "/",
    "schemes": [
        "http",
        "https"
    ]
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

SOIL_TYPES_LIST = ye.SOIL_TYPES
WATER_AVAILABILITY_LIST = ye.WATER_AVAILABILITY_OPTIONS
WATER_QUALITY_LIST = ye.WATER_QUALITY_OPTIONS
SEASONS_LIST = ye.SEASONS

@app.route('/')
def home():
    return render_template(
        "index.html",
        areas=ye.AVAILABLE_AREAS,
        crops=ye.AVAILABLE_CROPS,
        soil_types=SOIL_TYPES_LIST,
        water_availabilities=WATER_AVAILABILITY_LIST,
        water_qualities=WATER_QUALITY_LIST,
        seasons=SEASONS_LIST,
        user=current_user if current_user.is_authenticated else None
    )

# Authentication APIs

@app.route('/api/register', methods=['POST'])
def api_register():
    """
    User Registration Endpoint
    ---
    tags:
      - Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              example: john_farmer
            email:
              type: string
              example: john@farm.org
            password:
              type: string
              example: SecretPass123
            role:
              type: string
              example: Farmer
    responses:
      201:
        description: User created successfully
      400:
        description: User or email already exists or invalid data
    """
    try:
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        role = data.get('role', 'Farmer')
        remember = bool(data.get('remember', True))

        if not username or not email or not password:
            return jsonify({"status": "error", "message": "Username, email and password are required"}), 400

        if "@" not in email or "." not in email:
            return jsonify({"status": "error", "message": "Invalid email address format"}), 400

        if len(password) < 6:
            return jsonify({"status": "error", "message": "Password must be at least 6 characters long"}), 400

        if User.query.filter(User.username == username).first():
            return jsonify({"status": "error", "message": "Username already registered. Please choose another username or log in."}), 400

        if User.query.filter(User.email == email).first():
            return jsonify({"status": "error", "message": "Email already registered. Please log in with your credentials."}), 400

        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user, remember=remember)

        return jsonify({"status": "success", "message": "Registration successful", "user": user.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/login', methods=['POST'])
def api_login():
    """
    User Login Endpoint
    ---
    tags:
      - Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              example: john_farmer
            password:
              type: string
              example: SecretPass123
            remember:
              type: boolean
              example: true
    responses:
      200:
        description: Login successful
      401:
        description: Invalid credentials
    """
    try:
        data = request.get_json() or {}
        username_or_email = data.get('username', '').strip()
        password = data.get('password', '')
        remember = bool(data.get('remember', True))

        user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email.lower())).first()

        if not user or not user.check_password(password):
            return jsonify({"status": "error", "message": "Invalid username/email or password"}), 401

        login_user(user, remember=remember)
        return jsonify({"status": "success", "message": "Login successful", "user": user.to_dict()}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/user/reset-password', methods=['POST'])
def api_reset_password():
    """
    User Password Reset Endpoint
    ---
    tags:
      - Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              example: john@farm.org
            new_password:
              type: string
              example: NewSecretPass456
    responses:
      200:
        description: Password reset successfully
      400:
        description: Invalid data or user not found
    """
    try:
        data = request.get_json() or {}
        email = data.get('email', '').strip().lower()
        new_password = data.get('new_password', '')

        if not email or not new_password:
            return jsonify({"status": "error", "message": "Email address and new password are required"}), 400

        if len(new_password) < 6:
            return jsonify({"status": "error", "message": "New password must be at least 6 characters long"}), 400

        user = User.query.filter(User.email == email).first()
        if not user:
            return jsonify({"status": "error", "message": "No account found registered under this email address"}), 404

        user.set_password(new_password)
        db.session.commit()

        login_user(user, remember=True)
        return jsonify({"status": "success", "message": "Password reset successfully! You are now logged in.", "user": user.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/logout', methods=['GET', 'POST'])
def api_logout():
    """
    User Logout Endpoint
    ---
    tags:
      - Authentication
    responses:
      200:
        description: Logged out successfully
    """
    logout_user()
    return jsonify({"status": "success", "message": "Logged out successfully"}), 200

@app.route('/api/user/me', methods=['GET'])
def get_current_user_profile():
    """
    Get Current Authenticated User Session Profile
    ---
    tags:
      - Authentication
    responses:
      200:
        description: Current user profile or unauthenticated status
    """
    if current_user.is_authenticated:
        return jsonify({"status": "success", "authenticated": True, "user": current_user.to_dict()}), 200
    return jsonify({"status": "success", "authenticated": False, "user": None}), 200

@app.route('/api/user/change-password', methods=['POST'])
@login_required
def api_change_password():
    """
    Change Authenticated User Password
    ---
    tags:
      - Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            old_password:
              type: string
              example: SecretPass123
            new_password:
              type: string
              example: NewSecretPass456
    responses:
      200:
        description: Password updated successfully
      400:
        description: Incorrect old password or weak new password
    """
    try:
        data = request.get_json() or {}
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')

        if not old_password or not new_password:
            return jsonify({"status": "error", "message": "Old and new password are required"}), 400

        if not current_user.check_password(old_password):
            return jsonify({"status": "error", "message": "Incorrect current password"}), 400

        if len(new_password) < 6:
            return jsonify({"status": "error", "message": "New password must be at least 6 characters long"}), 400

        current_user.set_password(new_password)
        db.session.commit()

        return jsonify({"status": "success", "message": "Password changed successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400


# Saved Scenario Database APIs

@app.route('/api/scenarios/save', methods=['POST'])
def save_scenario():
    """
    Save Farm Yield & Financial Prediction Scenario to Database
    ---
    tags:
      - Saved Scenarios
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            scenario_name:
              type: string
              example: Kharif Rice 2024 Optimised
    responses:
      201:
        description: Scenario saved to database
    """
    try:
        data = request.get_json()
        
        scenario_name = data.get('scenario_name', f"Farm Scenario {datetime.utcnow().strftime('%b %d %H:%M')}")
        area = data.get('area', 'India')
        crop = data.get('crop', 'Wheat')
        farm_area = float(data.get('farm_area', 10.0))
        year = int(data.get('year', 2024))
        rainfall = float(data.get('rainfall', 1000))
        pesticides = float(data.get('pesticides', 150))
        temp = float(data.get('temp', 25))
        soil_type = data.get('soil_type', 'Loamy')
        water_availability = data.get('water_availability', 'Moderate (Seasonal Irrigation)')
        water_quality = data.get('water_quality', 'Optimal Freshwater (pH 6.5 - 7.5)')
        season = data.get('season', 'Kharif (Monsoon)')
        raw_mp = data.get('market_price')
        try:
            market_price = float(raw_mp) if raw_mp is not None and str(raw_mp).strip() != "" else 350.0
        except (ValueError, TypeError):
            market_price = 350.0

        # Re-run prediction or use payload metrics
        if 'total_yield_tonnes' in data:
            predicted_yield = float(data['total_yield_tonnes'])
            yield_per_ha = float(data.get('yield_per_ha_tonnes', predicted_yield / max(0.1, farm_area)))
            total_spending = float(data['total_spending'])
            net_profit = float(data['net_profit'])
            roi_percent = float(data['roi_percent'])
            agronomic_score = int(data.get('agronomic_score', 85))
        else:
            result = ye.predict_crop_yield_and_finance(
                area_name=area, item_name=crop, year=year, rainfall=rainfall,
                pesticides=pesticides, temp=temp, soil_type=soil_type,
                water_availability=water_availability, water_quality=water_quality,
                season=season, farm_area=farm_area, custom_market_price=market_price
            )
            predicted_yield = result['total_yield_tonnes']
            yield_per_ha = result['yield_per_ha_tonnes']
            total_spending = result['total_spending']
            net_profit = result['net_profit']
            roi_percent = result['roi_percent']
            agronomic_score = result['agronomic_score']

        user_id = current_user.id if current_user.is_authenticated else 1
        
        # Ensure default user if non-auth demo fallback
        if not current_user.is_authenticated and not db.session.get(User, 1):
            demo_user = User(id=1, username="demo_farmer", email="demo@agriyield.ai")
            demo_user.set_password("demo1234")
            db.session.add(demo_user)
            db.session.commit()

        scenario = SavedScenario(
            user_id=user_id,
            scenario_name=scenario_name,
            area=area,
            crop=crop,
            farm_area=farm_area,
            year=year,
            rainfall=rainfall,
            pesticides=pesticides,
            temp=temp,
            soil_type=soil_type,
            water_availability=water_availability,
            water_quality=water_quality,
            season=season,
            market_price=market_price,
            predicted_yield=predicted_yield,
            yield_per_ha=yield_per_ha,
            total_spending=total_spending,
            net_profit=net_profit,
            roi_percent=roi_percent,
            agronomic_score=agronomic_score
        )

        db.session.add(scenario)
        db.session.commit()

        return jsonify({"status": "success", "message": "Scenario saved to database", "scenario": scenario.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/scenarios', methods=['GET'])
def get_scenarios():
    """
    Fetch Saved Farm Scenarios from Database
    ---
    tags:
      - Saved Scenarios
    responses:
      200:
        description: List of saved scenarios
    """
    try:
        user_id = current_user.id if current_user.is_authenticated else None
        if user_id:
            scenarios = SavedScenario.query.filter_by(user_id=user_id).order_by(SavedScenario.created_at.desc()).all()
        else:
            scenarios = SavedScenario.query.order_by(SavedScenario.created_at.desc()).limit(20).all()

        return jsonify({"status": "success", "scenarios": [s.to_dict() for s in scenarios]}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/scenarios/<int:scenario_id>', methods=['DELETE'])
def delete_scenario(scenario_id):
    """
    Delete Saved Farm Scenario from Database
    ---
    tags:
      - Saved Scenarios
    parameters:
      - name: scenario_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Scenario deleted successfully
    """
    try:
        scenario = db.session.get(SavedScenario, scenario_id)
        if not scenario:
            return jsonify({"status": "error", "message": "Scenario not found"}), 404

        if current_user.is_authenticated and scenario.user_id != current_user.id and getattr(current_user, 'role', '') != "Admin":
            return jsonify({"status": "error", "message": "Unauthorized to delete another user's scenario"}), 403

        db.session.delete(scenario)
        db.session.commit()
        return jsonify({"status": "success", "message": "Scenario deleted"}), 200
    except Exception as e:

        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health Check & Model Monitoring Endpoint
    ---
    tags:
      - System Monitoring
    responses:
      200:
        description: System is healthy, DB connection OK, and ML model is ready
      500:
        description: System is unhealthy or ML model failed to load
    """
    try:
        is_model_ready = ye.model is not None and len(ye.AVAILABLE_AREAS) > 0
        db_ready = True
        try:
            db.session.execute(db.select(User).limit(1))
        except Exception:
            db_ready = False

        return jsonify({
            "status": "healthy" if (is_model_ready and db_ready) else "unhealthy",
            "model_loaded": is_model_ready,
            "database_connected": db_ready,
            "available_crops_count": len(ye.AVAILABLE_CROPS),
            "available_areas_count": len(ye.AVAILABLE_AREAS)
        }), 200 if (is_model_ready and db_ready) else 500
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/api/crop_defaults/<crop_name>', methods=['GET'])
def get_crop_defaults(crop_name):
    """
    Get Financial Defaults for Specific Crop
    ---
    tags:
      - Crop Financials
    parameters:
      - name: crop_name
        in: path
        type: string
        required: true
        description: Target crop name (e.g. Wheat, Rice, paddy, Potatoes)
        example: Wheat
    responses:
      200:
        description: Default market price, seed costs, and fertilizer costs
    """
    defaults = ye.CROP_FINANCIAL_DEFAULTS.get(crop_name, {"market_price": 350.0, "seed_cost": 100.0, "base_fertilizer": 120.0})
    return jsonify({
        "status": "success",
        "crop": crop_name,
        "default_market_price": defaults["market_price"],
        "default_seed_cost": defaults["seed_cost"]
    })

@app.route('/api/predict', methods=['POST'])
def api_predict():
    """
    Predict Crop Yield & Complete Financial Analytics
    ---
    tags:
      - Predictions
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            area:
              type: string
              example: India
            crop:
              type: string
              example: Wheat
            year:
              type: number
              example: 2024
            rainfall:
              type: number
              example: 1200
            pesticides:
              type: number
              example: 150
            temp:
              type: number
              example: 25
            soil_type:
              type: string
              example: Loamy
            water_availability:
              type: string
              example: Moderate (Seasonal Irrigation)
            water_quality:
              type: string
              example: Optimal Freshwater (pH 6.5 - 7.5)
            season:
              type: string
              example: Kharif (Monsoon)
            farm_area:
              type: number
              example: 10
            market_price:
              type: number
              example: 350
    responses:
      200:
        description: Yield prediction in Tonnes, spending breakdown, net profit & ROI
      400:
        description: Invalid parameters or prediction failure
    """
    try:
        data = request.get_json() if request.is_json else request.form
        
        area = data.get('area', 'India')
        crop = data.get('crop', data.get('item', 'Wheat'))
        year = float(data.get('year', 2024))
        rainfall = float(data.get('rainfall', 1000))
        pesticides = float(data.get('pesticides', 150))
        temp = float(data.get('temp', 25))
        soil_type = data.get('soil_type', 'Loamy')
        water_availability = data.get('water_availability', 'Moderate (Seasonal Irrigation)')
        water_quality = data.get('water_quality', 'Optimal Freshwater (pH 6.5 - 7.5)')
        season = data.get('season', 'Kharif (Monsoon)')
        farm_area = float(data.get('farm_area', 10.0))
        raw_mp = data.get('market_price')
        try:
            market_price = float(raw_mp) if raw_mp is not None and str(raw_mp).strip() != "" else None
        except (ValueError, TypeError):
            market_price = None

        result = ye.predict_crop_yield_and_finance(
            area_name=area,
            item_name=crop,
            year=year,
            rainfall=rainfall,
            pesticides=pesticides,
            temp=temp,
            soil_type=soil_type,
            water_availability=water_availability,
            water_quality=water_quality,
            season=season,
            farm_area=farm_area,
            custom_market_price=market_price
        )

        return jsonify({"status": "success", "data": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/predict', methods=['POST'])
def predict_form():
    area = request.form.get('area', 'India')
    crop = request.form.get('crop', request.form.get('item', 'Wheat'))
    year = float(request.form.get('year', 2024))
    rainfall = float(request.form.get('rainfall', 1000))
    pesticides = float(request.form.get('pesticides', 150))
    temp = float(request.form.get('temp', 25))
    soil_type = request.form.get('soil_type', 'Loamy')
    water_availability = request.form.get('water_availability', 'Moderate (Seasonal Irrigation)')
    water_quality = request.form.get('water_quality', 'Optimal Freshwater (pH 6.5 - 7.5)')
    season = request.form.get('season', 'Kharif (Monsoon)')
    farm_area = float(request.form.get('farm_area', 10.0))
    raw_mp = request.form.get('market_price')
    try:
        market_price = float(raw_mp) if raw_mp is not None and str(raw_mp).strip() != "" else None
    except (ValueError, TypeError):
        market_price = None

    result = ye.predict_crop_yield_and_finance(
        area_name=area,
        item_name=crop,
        year=year,
        rainfall=rainfall,
        pesticides=pesticides,
        temp=temp,
        soil_type=soil_type,
        water_availability=water_availability,
        water_quality=water_quality,
        season=season,
        farm_area=farm_area,
        custom_market_price=market_price
    )

    return render_template(
        "index.html",
        areas=ye.AVAILABLE_AREAS,
        crops=ye.AVAILABLE_CROPS,
        soil_types=SOIL_TYPES_LIST,
        water_availabilities=WATER_AVAILABILITY_LIST,
        water_qualities=WATER_QUALITY_LIST,
        seasons=SEASONS_LIST,
        initial_result=result,
        user=current_user if current_user.is_authenticated else None
    )

@app.route('/api/export_csv', methods=['POST'])
def export_csv():
    """
    Export Yield and Profit Report to CSV
    ---
    tags:
      - Reports
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
    responses:
      200:
        description: CSV file response
    """
    try:
        data = request.get_json()
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["AI Crop Yield & Profit Analytics Report"])
        writer.writerow([])
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Location / Area", data.get("area")])
        writer.writerow(["Selected Crop", data.get("crop")])
        writer.writerow(["Farm Size (Ha)", data.get("farm_area_ha")])
        writer.writerow(["Yield per Hectare (Tonnes/Ha)", data.get("yield_per_ha_tonnes")])
        writer.writerow(["Total Predicted Yield (Tonnes)", data.get("total_yield_tonnes")])
        writer.writerow(["Agronomic Health Score (%)", f"{data.get('agronomic_score')}%"])
        writer.writerow(["Total Spending ($)", f"${data.get('total_spending')}"])
        writer.writerow(["Gross Revenue ($)", f"${data.get('gross_revenue')}"])
        writer.writerow(["Net Profit ($)", f"${data.get('net_profit')}"])
        writer.writerow(["ROI (%)", f"{data.get('roi_percent')}%"])
        writer.writerow(["Break-even Price ($/Tonne)", f"${data.get('breakeven_price')}"])

        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=crop_yield_financial_report.csv"
        response.headers["Content-type"] = "text/csv"
        return response
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/weather', methods=['GET'])
def get_weather():
    """
    Get Regional Weather & Agro-Climatic Intelligence
    ---
    tags:
      - Weather Intelligence
    parameters:
      - name: area
        in: query
        type: string
        required: false
        default: India
        description: Country or area name
    responses:
      200:
        description: Weather metrics and agricultural risk assessment
    """
    area = request.args.get('area', 'India')
    weather_data = ye.get_weather_data(area)
    return jsonify({"status": "success", "data": weather_data}), 200

@app.route('/api/scenarios/compare', methods=['POST'])
def compare_scenarios_endpoint():
    """
    Compare Multiple Farm Scenarios Side-by-Side
    ---
    tags:
      - Saved Scenarios
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            scenario_ids:
              type: array
              items:
                type: integer
              example: [1, 2]
            scenarios:
              type: array
              items:
                type: object
    responses:
      200:
        description: Comparison results and ranking highlights
    """
    try:
        data = request.get_json() or {}
        scenario_ids = data.get('scenario_ids', [])
        scenarios_payload = data.get('scenarios', [])

        target_list = []
        if scenario_ids:
            for s_id in scenario_ids:
                scen = db.session.get(SavedScenario, s_id)
                if scen:
                    target_list.append(scen.to_dict())

        if scenarios_payload:
            target_list.extend(scenarios_payload)

        if not target_list:
            return jsonify({"status": "error", "message": "No valid scenarios or scenario_ids provided"}), 400

        result = ye.compare_scenarios(target_list)
        return jsonify({"status": "success", "data": result}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/optimize', methods=['POST'])
def optimize_portfolio_endpoint():
    """
    Optimize Multi-Crop Land Allocation Portfolio
    ---
    tags:
      - Crop Analytics & Optimization
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            total_farm_area:
              type: number
              example: 50
            budget:
              type: number
              example: 25000
            soil_type:
              type: string
              example: Loamy
            area:
              type: string
              example: India
            candidate_crops:
              type: array
              items:
                type: string
              example: ["Wheat", "Rice, paddy", "Maize"]
    responses:
      200:
        description: Optimized land allocation, costs, projected yield, and returns
    """
    try:
        data = request.get_json() or {}
        total_farm_area = float(data.get('total_farm_area', 10.0))
        budget = float(data.get('budget', 0.0))
        soil_type = data.get('soil_type', 'Loamy')
        area = data.get('area', 'India')
        candidate_crops = data.get('candidate_crops', None)

        res = ye.optimize_crop_portfolio(
            total_farm_area=total_farm_area,
            budget=budget,
            soil_type=soil_type,
            area_name=area,
            candidate_crops=candidate_crops
        )
        return jsonify(res), 200 if res.get("status") == "success" else 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/analytics/summary', methods=['GET'])
def get_analytics_summary():
    """
    Get Aggregate Analytics Summary of Saved Scenarios
    ---
    tags:
      - Saved Scenarios
    responses:
      200:
        description: Aggregate statistics across scenarios
    """
    try:
        user_id = current_user.id if current_user.is_authenticated else None
        if user_id:
            scenarios = SavedScenario.query.filter_by(user_id=user_id).all()
        else:
            scenarios = SavedScenario.query.all()

        if not scenarios:
            return jsonify({
                "status": "success",
                "total_scenarios": 0,
                "total_modeled_area_ha": 0,
                "total_projected_profit": 0,
                "average_roi_percent": 0,
                "top_crop_by_frequency": None
            }), 200

        total_area = sum(s.farm_area for s in scenarios)
        total_profit = sum(s.net_profit for s in scenarios)
        avg_roi = sum(s.roi_percent for s in scenarios) / len(scenarios)

        crop_counts = {}
        for s in scenarios:
            crop_counts[s.crop] = crop_counts.get(s.crop, 0) + 1
        top_crop = max(crop_counts, key=crop_counts.get) if crop_counts else None

        return jsonify({
            "status": "success",
            "total_scenarios": len(scenarios),
            "total_modeled_area_ha": round(total_area, 2),
            "total_projected_profit": round(total_profit, 2),
            "average_roi_percent": round(avg_roi, 1),
            "top_crop_by_frequency": top_crop
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/monitoring/drift', methods=['GET'])
def get_model_drift_metrics():
    """
    Evidently AI Model Performance & Data Drift Monitoring Endpoint
    ---
    tags:
      - MLOps & Model Monitoring
    responses:
      200:
        description: Data drift metrics, drift score, and feature-level statistical shifts
    """
    try:
        scenarios = SavedScenario.query.all()
        summary = mm.get_drift_metrics_summary(scenarios=scenarios)
        return jsonify(summary), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/monitoring/report', methods=['GET'])
def serve_evidently_html_report():
    """
    Interactive Evidently AI Dashboard HTML Report Endpoint
    ---
    tags:
      - MLOps & Model Monitoring
    responses:
      200:
        description: Serves interactive Evidently HTML monitoring report
    """
    try:
        report_path = mm.run_evidently_drift_report("evidently_drift_report.html")
        return send_file(report_path, mimetype='text/html')
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(host=host, port=port, debug=debug)