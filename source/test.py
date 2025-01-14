import mlflow
import numpy as np
from sklearn.datasets import load_iris
from sklearn.metrics import accuracy_score
import os

def test_model(model_alias):
    # Load test data
    iris = load_iris()
    X_test = iris.data[::3]  # Use every third sample for testing
    y_test = iris.target[::3]
    
    # Load model from MLflow
    mlflow.set_tracking_uri(os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000'))
    model = mlflow.pyfunc.load_model(f"models:/iris_model@{model_alias}")
    
    # Make predictions
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    # Define threshold
    ACCURACY_THRESHOLD = 0.9
    
    if accuracy < ACCURACY_THRESHOLD:
        raise Exception(f"Model accuracy {accuracy:.4f} below threshold {ACCURACY_THRESHOLD}")
        
    return accuracy

if __name__ == "__main__":
    accuracy = test_model("Challenger")
    print(f"Test accuracy: {accuracy:.4f}")