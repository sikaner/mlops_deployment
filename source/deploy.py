import mlflow
import os
import sys
import boto3
from botocore.exceptions import NoCredentialsError

def deploy_model(model_alias, Staging):
    mlflow.set_tracking_uri(os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000'))
    client = mlflow.tracking.MlflowClient()
    
    # Get the model version for the given alias
    model_version = client.get_model_version_by_alias("iris_model", model_alias)
    
    # Transition the model to the specified stage
    client.transition_model_version_stage(
        name="iris_model",
        version=model_version.version,
        stage=Staging
    )
    
    print(f"Model version {model_version.version} transitioned to {Staging}")
    return True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python deploy.py <model_alias> <stage>")
        sys.exit(1)
        
    deploy_model(sys.argv[1], sys.argv[2])