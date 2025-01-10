import mlflow
import mlflow.sklearn
from sklearn.datasets import load_iris
from sklearn.metrics import accuracy_score
import sys

def test_model(environment):
    mlflow.set_tracking_uri("http://localhost:5000")
    client = mlflow.tracking.MlflowClient()
    
    # Load the appropriate model based on environment
    if environment == "dev":
        model_alias = "Challenger"
    elif environment == "preprod":
        model_alias = "Challenger-pre-test"
    else:
        raise ValueError("Invalid environment specified")
    
    # Load model
    model = mlflow.sklearn.load_model(f"models:/iris_classifier@{model_alias}")
    
    # Load test data
    iris = load_iris()
    X_test = iris.data
    y_test = iris.target
    
    # Make predictions
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    
    # Define threshold based on environment
    threshold = 0.9 if environment == "preprod" else 0.8
    
    if accuracy >= threshold:
        print(f"Test passed with accuracy: {accuracy}")
        return True
    else:
        print(f"Test failed. Accuracy {accuracy} below threshold {threshold}")
        return False

if __name__ == "__main__":
    environment = sys.argv[1]
    success = test_model(environment)
    sys.exit(0 if success else 1)