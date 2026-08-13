from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), default="Farmer")
    preferred_area = db.Column(db.String(100), default="India")
    default_farm_area_ha = db.Column(db.Float, default=10.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    scenarios = db.relationship('SavedScenario', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "preferred_area": self.preferred_area,
            "default_farm_area_ha": self.default_farm_area_ha,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else ""
        }


class SavedScenario(db.Model):
    __tablename__ = 'saved_scenario'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    scenario_name = db.Column(db.String(120), nullable=False)
    area = db.Column(db.String(100), nullable=False)
    crop = db.Column(db.String(100), nullable=False)
    farm_area = db.Column(db.Float, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    rainfall = db.Column(db.Float, nullable=False)
    pesticides = db.Column(db.Float, nullable=False)
    temp = db.Column(db.Float, nullable=False)
    soil_type = db.Column(db.String(50), nullable=False)
    water_availability = db.Column(db.String(100), nullable=False)
    water_quality = db.Column(db.String(100), nullable=False)
    season = db.Column(db.String(100), nullable=False)
    market_price = db.Column(db.Float, nullable=False)
    
    # Calculated Yield and Financial Metrics
    predicted_yield = db.Column(db.Float, nullable=False)
    yield_per_ha = db.Column(db.Float, nullable=False)
    total_spending = db.Column(db.Float, nullable=False)
    net_profit = db.Column(db.Float, nullable=False)
    roi_percent = db.Column(db.Float, nullable=False)
    agronomic_score = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "scenario_name": self.scenario_name,
            "area": self.area,
            "crop": self.crop,
            "farm_area": self.farm_area,
            "year": self.year,
            "rainfall": self.rainfall,
            "pesticides": self.pesticides,
            "temp": self.temp,
            "soil_type": self.soil_type,
            "water_availability": self.water_availability,
            "water_quality": self.water_quality,
            "season": self.season,
            "market_price": self.market_price,
            "predicted_yield": self.predicted_yield,
            "yield_per_ha": self.yield_per_ha,
            "total_spending": self.total_spending,
            "net_profit": self.net_profit,
            "roi_percent": self.roi_percent,
            "agronomic_score": self.agronomic_score,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else ""
        }
