import mlflow
import mlflow.sklearn
import sys

def deploy_model(environment):
    mlflow.set_tracking_uri("http://localhost:5000")
    client = mlflow.tracking.MlflowClient()
    
    # Set the appropriate alias based on environment
    if environment == "dev":
        source_alias = "Challenger"
        target_alias = "Challenger-pre-test"
    elif environment == "preprod":
        source_alias = "Challenger-pre-test"
        target_alias = "Challenger-post-test"
    elif environment == "prod":
        source_alias = "Challenger-post-test"
        target_alias = "Champion"
    else:
        raise ValueError("Invalid environment specified")
    
    # Get the model version for the source alias
    model_version = client.get_model_version_by_alias("iris_classifier", source_alias)
    
    # Update the alias for the target environment
    client.set_registered_model_alias(
        name="iris_classifier",
        alias=target_alias,
        version=model_version.version
    )
    
    print(f"Model deployed to {environment} environment with alias {target_alias}")
    return True

if __name__ == "__main__":
    environment = sys.argv[1]
    success = deploy_model(environment)
    sys.exit(0 if success else 1)