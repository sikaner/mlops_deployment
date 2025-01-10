import mlflow
import mlflow.sklearn
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import os

def train_model():
    # Set MLflow tracking URI
    mlflow.set_tracking_uri("http://localhost:5000")
    
    # Start MLflow run
    with mlflow.start_run(run_name="dev_training") as run:
        # Load data
        iris = load_iris()
        
        X = iris.data
        y = iris.target
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train model
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X_train, y_train)
        
        # Make predictions and calculate accuracy
        predictions = rf.predict(X_test)
        accuracy = accuracy_score(y_test, predictions)
        
        # Log parameters and metrics
        mlflow.log_param("n_estimators", 100)
        mlflow.log_metric("accuracy", accuracy)
        
        # Register model
        mlflow.sklearn.log_model(rf, "model")
        
        # Register model in MLflow Model Registry
        model_uri = f"runs:/{run.info.run_id}/model"
        model_details = mlflow.register_model(model_uri, "iris_classifier")
        
        # Set alias
        client = mlflow.tracking.MlflowClient()
        client.set_registered_model_alias(name="iris_classifier", 
                                        alias="Challenger",
                                        version=model_details.version)
        
        return accuracy

if __name__ == "__main__":
    accuracy = train_model()
    print(f"Model trained with accuracy: {accuracy}")