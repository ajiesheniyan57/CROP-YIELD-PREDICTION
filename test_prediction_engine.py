import unittest
import json
import yield_engine as ye
from app import app

class TestCropYieldPredictionSystem(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_yield_engine_direct_prediction(self):
        res = ye.predict_crop_yield_and_finance(
            area_name="India",
            item_name="Wheat",
            year=2024,
            rainfall=1100,
            pesticides=150,
            temp=24,
            soil_type="Loamy",
            water_availability="High (Canal / Drip Irrigation)",
            water_quality="Optimal Freshwater (pH 6.5 - 7.5)",
            season="Rabi (Winter)",
            farm_area=10.0,
            custom_market_price=350.0
        )

        self.assertIn("total_yield_tonnes", res)
        self.assertIn("total_spending", res)
        self.assertIn("net_profit", res)
        self.assertIn("roi_percent", res)

        self.assertGreater(res["total_yield_tonnes"], 0)
        self.assertGreater(res["total_spending"], 0)
        self.assertAlmostEqual(res["gross_revenue"], res["total_yield_tonnes"] * 350.0, delta=2.0)
        self.assertAlmostEqual(res["net_profit"], res["gross_revenue"] - res["total_spending"], delta=1.0)

    def test_api_predict_endpoint(self):
        payload = {
            "area": "India",
            "crop": "Rice, paddy",
            "year": 2024,
            "farm_area": 12,
            "rainfall": 1600,
            "temp": 28,
            "pesticides": 200,
            "soil_type": "Clay",
            "water_availability": "High (Canal / Drip Irrigation)",
            "water_quality": "Optimal Freshwater (pH 6.5 - 7.5)",
            "season": "Kharif (Monsoon)",
            "market_price": 400
        }

        response = self.app.post('/api/predict', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("total_yield_tonnes", data["data"])
        self.assertIn("total_spending", data["data"])
        self.assertIn("net_profit", data["data"])

    def test_crop_defaults_endpoint(self):
        response = self.app.get('/api/crop_defaults/Wheat')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["crop"], "Wheat")
        self.assertIn("default_market_price", data)

    def test_export_csv_endpoint(self):
        sample_data = {
            "area": "India",
            "crop": "Wheat",
            "farm_area_ha": 10,
            "yield_per_ha_tonnes": 3.1,
            "total_yield_tonnes": 31.0,
            "agronomic_score": 88,
            "total_spending": 8400.0,
            "gross_revenue": 10850.0,
            "net_profit": 2450.0,
            "roi_percent": 29.1,
            "breakeven_price": 270.97
        }

        response = self.app.post('/api/export_csv', data=json.dumps(sample_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response.headers["Content-Type"])

    def test_health_check_endpoint(self):
        response = self.app.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["model_loaded"])
        self.assertGreater(data["available_crops_count"], 0)

    def test_swagger_docs_endpoint(self):
        response = self.app.get('/api/docs/')
        self.assertEqual(response.status_code, 200)

        spec_response = self.app.get('/apispec_1.json')
        self.assertEqual(spec_response.status_code, 200)
        spec_data = json.loads(spec_response.data)
        self.assertIn("swagger", spec_data)

    def test_user_authentication_flow(self):
        import time
        unique_username = f"farmer_{int(time.time())}"
        unique_email = f"farmer_{int(time.time())}@agriyield.ai"

        # 1. Register User
        reg_payload = {
            "username": unique_username,
            "email": unique_email,
            "password": "Password123!",
            "role": "Farmer"
        }
        response = self.app.post('/api/register', data=json.dumps(reg_payload), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")

        # 2. Check current user profile session
        me_response = self.app.get('/api/user/me')
        me_data = json.loads(me_response.data)
        self.assertTrue(me_data["authenticated"])
        self.assertEqual(me_data["user"]["username"], unique_username)

        # 3. Logout User
        logout_response = self.app.get('/api/logout')
        self.assertEqual(logout_response.status_code, 200)

        # 4. Login User
        login_payload = {
            "username": unique_username,
            "password": "Password123!"
        }
        login_response = self.app.post('/api/login', data=json.dumps(login_payload), content_type='application/json')
        self.assertEqual(login_response.status_code, 200)
        login_data = json.loads(login_response.data)
        self.assertEqual(login_data["status"], "success")

    def test_database_scenario_save_and_fetch_delete(self):
        scenario_payload = {
            "scenario_name": "Test Kharif Paddy Farm",
            "area": "India",
            "crop": "Rice, paddy",
            "farm_area": 15,
            "year": 2024,
            "rainfall": 1500,
            "pesticides": 180,
            "temp": 28,
            "soil_type": "Clay",
            "water_availability": "High (Canal / Drip Irrigation)",
            "water_quality": "Optimal Freshwater (pH 6.5 - 7.5)",
            "season": "Kharif (Monsoon)",
            "market_price": 390
        }

        # 1. Save Scenario
        save_res = self.app.post('/api/scenarios/save', data=json.dumps(scenario_payload), content_type='application/json')
        self.assertEqual(save_res.status_code, 201)
        save_data = json.loads(save_res.data)
        self.assertEqual(save_data["status"], "success")
        scenario_id = save_data["scenario"]["id"]

        # 2. Fetch Scenarios from Database
        fetch_res = self.app.get('/api/scenarios')
        self.assertEqual(fetch_res.status_code, 200)
        fetch_data = json.loads(fetch_res.data)
        self.assertGreater(len(fetch_data["scenarios"]), 0)

        # 3. Delete Scenario
        del_res = self.app.delete(f'/api/scenarios/{scenario_id}')
        self.assertEqual(del_res.status_code, 200)

    def test_weather_integration_endpoint(self):
        response = self.app.get('/api/weather?area=India')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["data"]["area"], "India")
        self.assertIn("temperature_celsius", data["data"])
        self.assertIn("risk_alerts", data["data"])

    def test_scenario_comparison_endpoint(self):
        payload = {
            "scenarios": [
                {
                    "scenario_name": "Wheat Baseline",
                    "area": "India",
                    "crop": "Wheat",
                    "farm_area": 10,
                    "rainfall": 1000,
                    "pesticides": 150,
                    "temp": 25,
                    "soil_type": "Loamy",
                    "market_price": 350
                },
                {
                    "scenario_name": "Paddy High Yield",
                    "area": "India",
                    "crop": "Rice, paddy",
                    "farm_area": 10,
                    "rainfall": 1600,
                    "pesticides": 200,
                    "temp": 28,
                    "soil_type": "Clay",
                    "market_price": 420
                }
            ]
        }
        response = self.app.post('/api/scenarios/compare', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["data"]["compared_scenarios_count"], 2)
        self.assertIn("summary_highlights", data["data"])
        self.assertIn("top_roi", data["data"]["summary_highlights"])

    def test_crop_portfolio_optimizer_endpoint(self):
        payload = {
            "total_farm_area": 25,
            "budget": 15000,
            "soil_type": "Loamy",
            "area": "India",
            "candidate_crops": ["Wheat", "Rice, paddy", "Maize"]
        }
        response = self.app.post('/api/optimize', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["total_farm_area_ha"], 25)
        self.assertGreater(len(data["allocations"]), 0)

    def test_analytics_summary_endpoint(self):
        response = self.app.get('/api/analytics/summary')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("total_scenarios", data)

    def test_evidently_drift_metrics_endpoint(self):
        response = self.app.get('/api/monitoring/drift')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("dataset_drift_summary", data)
        self.assertIn("feature_metrics", data)
        self.assertIn("rainfall", data["feature_metrics"])

    def test_evidently_report_endpoint(self):
        response = self.app.get('/api/monitoring/report')
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["Content-Type"])
        self.assertIn(b"Evidently", response.data)

    def test_registration_validation_rules(self):
        # 1. Invalid email format
        bad_email_payload = {
            "username": "bad_email_user",
            "email": "invalidemailformat",
            "password": "Password123!",
            "role": "Farmer"
        }
        res1 = self.app.post('/api/register', data=json.dumps(bad_email_payload), content_type='application/json')
        self.assertEqual(res1.status_code, 400)
        data1 = json.loads(res1.data)
        self.assertEqual(data1["status"], "error")

        # 2. Weak password (< 6 chars)
        weak_pass_payload = {
            "username": "weak_pass_user",
            "email": "weak@agriyield.ai",
            "password": "123",
            "role": "Farmer"
        }
        res2 = self.app.post('/api/register', data=json.dumps(weak_pass_payload), content_type='application/json')
        self.assertEqual(res2.status_code, 400)
        data2 = json.loads(res2.data)
        self.assertEqual(data2["status"], "error")

    def test_user_password_change_flow(self):
        import time
        ts = int(time.time())
        uname = f"passuser_{ts}"
        email = f"passuser_{ts}@agriyield.ai"

        # 1. Register & login automatically
        reg_payload = {"username": uname, "email": email, "password": "InitialPassword123", "role": "Farmer"}
        self.app.post('/api/register', data=json.dumps(reg_payload), content_type='application/json')

        # 2. Change password
        chg_payload = {"old_password": "InitialPassword123", "new_password": "NewSecurePassword456"}
        chg_res = self.app.post('/api/user/change-password', data=json.dumps(chg_payload), content_type='application/json')
        self.assertEqual(chg_res.status_code, 200)

        # 3. Logout
        self.app.get('/api/logout')

        # 4. Login with old password (should fail)
        fail_login = self.app.post('/api/login', data=json.dumps({"username": uname, "password": "InitialPassword123"}), content_type='application/json')
        self.assertEqual(fail_login.status_code, 401)

        # 5. Login with new password (should succeed)
        succ_login = self.app.post('/api/login', data=json.dumps({"username": uname, "password": "NewSecurePassword456"}), content_type='application/json')
        self.assertEqual(succ_login.status_code, 200)

    def test_scenario_deletion_security(self):
        import time
        ts = int(time.time())

        # Register User A
        uA = f"userA_{ts}"
        self.app.post('/api/register', data=json.dumps({"username": uA, "email": f"{uA}@farm.org", "password": "Pass123!UserA", "role": "Farmer"}), content_type='application/json')

        # User A saves scenario
        scenario_payload = {
            "scenario_name": "User A Private Farm",
            "area": "India",
            "crop": "Wheat",
            "farm_area": 10,
            "year": 2024,
            "rainfall": 1000,
            "pesticides": 150,
            "temp": 25,
            "soil_type": "Loamy",
            "water_availability": "High (Canal / Drip Irrigation)",
            "water_quality": "Optimal Freshwater (pH 6.5 - 7.5)",
            "season": "Kharif (Monsoon)",
            "market_price": 350
        }
        save_res = self.app.post('/api/scenarios/save', data=json.dumps(scenario_payload), content_type='application/json')
        scen_id = json.loads(save_res.data)["scenario"]["id"]

        # Logout User A
        self.app.get('/api/logout')

        # Register & Login User B
        uB = f"userB_{ts}"
        self.app.post('/api/register', data=json.dumps({"username": uB, "email": f"{uB}@farm.org", "password": "Pass123!UserB", "role": "Farmer"}), content_type='application/json')

        # User B attempts to delete User A's scenario (Forbidden 403)
        del_res = self.app.delete(f'/api/scenarios/{scen_id}')
        self.assertEqual(del_res.status_code, 403)

    def test_remember_token_and_reset_password_flow(self):
        import time
        ts = int(time.time())
        uname = f"remember_user_{ts}"
        email = f"remember_{ts}@agriyield.ai"

        # 1. Register with remember=True
        reg_payload = {
            "username": uname,
            "email": email,
            "password": "PassRemember123!",
            "role": "Farmer",
            "remember": True
        }
        res = self.app.post('/api/register', data=json.dumps(reg_payload), content_type='application/json')
        self.assertEqual(res.status_code, 201)
        headers = dict(res.headers)
        self.assertIn("Set-Cookie", headers)

        # 2. Reset password via endpoint
        reset_payload = {
            "email": email,
            "new_password": "ResetPassNew456!"
        }
        reset_res = self.app.post('/api/user/reset-password', data=json.dumps(reset_payload), content_type='application/json')
        self.assertEqual(reset_res.status_code, 200)
        reset_data = json.loads(reset_res.data)
        self.assertEqual(reset_data["status"], "success")

        # 3. Logout & Login with new reset password
        self.app.get('/api/logout')
        login_res = self.app.post('/api/login', data=json.dumps({"username": email, "password": "ResetPassNew456!", "remember": True}), content_type='application/json')
        self.assertEqual(login_res.status_code, 200)

if __name__ == '__main__':
    unittest.main()





