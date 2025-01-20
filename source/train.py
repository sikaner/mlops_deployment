import mlflow
import pandas as pd
import json
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import boto3
from botocore.exceptions import NoCredentialsError
import os

def train_model():
    # Load and prepare data
    iris = load_iris()
    X = pd.DataFrame(iris.data, columns=iris.feature_names)
    y = iris.target
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Initialize and train model
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)
    
    # Make predictions and calculate metrics
    y_pred = rf_model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    # Log with MLflow
    mlflow.set_tracking_uri(os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000'))
    mlflow.set_experiment("iris-classification")
    
    with mlflow.start_run() as run:
        # Log parameters
        mlflow.log_param("n_estimators", 100)
        
        # Log metrics
        mlflow.log_metric("accuracy", accuracy)
        
        # Log model
        mlflow.sklearn.log_model(
            rf_model, 
            "model",
            registered_model_name="iris_model"
        )
        
        # Set model alias
        client = mlflow.tracking.MlflowClient()
        model_version = client.get_latest_versions("iris_model", stages=["None"])[0].version
        client.set_registered_model_alias("iris_model", "Challenger", model_version)
        
    return accuracy, run.info.run_id


def predict_with_model(model_uri, data):
    # Load model from the registered model path
    model = mlflow.sklearn.load_model(model_uri)

    # Ensure the input dataframe has the correct column names in the right order
    expected_columns = ["petal length (cm)", "petal width (cm)", "sepal length (cm)", "sepal width (cm)"]
    data = data[expected_columns]

    # Make predictions
    predictions = model.predict(data)
    return predictions


if __name__ == "__main__":
    accuracy, run_id = train_model()
    print(f"Model trained with accuracy: {accuracy:.4f}")
    print(f"Run ID: {run_id}")

    # Example of using the trained model for inference
    sample_data = pd.DataFrame([[5.1, 3.5, 1.4, 0.2]], columns=["petal length (cm)", "petal width (cm)", "sepal length (cm)", "sepal width (cm)"])
    
    # Predict using the model
    predictions = predict_with_model(f"runs:/{run_id}/model", sample_data)
    print("Predictions:", predictions)
