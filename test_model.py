import joblib
import numpy as np

model = joblib.load("crop_yield_model.pkl")

sample = np.array([[0, 0, 2015, 1200, 200, 25]])

prediction = model.predict(sample)

print("Prediction:", prediction[0])