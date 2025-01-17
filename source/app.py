import os
import mlflow
import mlflow.pyfunc
from flask import Flask, request, jsonify
import pandas as pd

# Define the MLflow Tracking Server URI
MLFLOW_TRACKING_URI = "http://localhost:5000"
MODEL_NAME = "iris_model"
MODEL_VERSION = "10"  # Update this if a new version is deployed

# Set the MLflow Tracking URI
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

# Load the model from MLflow Registry
model_uri = f"models:/{MODEL_NAME}/{MODEL_VERSION}"
model = mlflow.pyfunc.load_model(model_uri)

# Initialize Flask app
app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"message": "MLflow Model Serving is Active!"})

# Define the prediction route
@app.route("/predict", methods=["POST"])
def predict():
    try:
        # Receive JSON data from the request
        data = request.get_json()

        # Convert input JSON to pandas DataFrame
        df = pd.DataFrame(data)

        # Make prediction
        predictions = model.predict(df)

        # Return the prediction results
        return jsonify({"predictions": predictions.tolist()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=True)
