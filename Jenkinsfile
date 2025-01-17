@Library('jenkins-shared-library') _

pipeline {
    agent any
    
    environment {
        MLFLOW_TRACKING_URI = 'http://localhost:5000'
        VIRTUAL_ENV = "${WORKSPACE}/.mldenv"
        PATH = "${VIRTUAL_ENV}/bin:${PATH}"
        AWS_DEFAULT_REGION = 'us-east-1'
        MODEL_NAME = 'iris_model'
    }

    stages {
        stage('Setup') {
            steps {
                withCredentials([[
                    $class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: 'aws-credentials-id',
                    accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                    secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                ]]) {
                    script {
                        try {
                            sh '''#!/bin/bash
                                set -e
                                set -x  
                                
                                echo "Checking Python installation..."
                                PYTHON_BIN=$(which python3 || true)
                                if [ -z "$PYTHON_BIN" ]; then
                                    echo "Python not found. Ensure Python is installed."
                                    exit 1
                                fi
                                $PYTHON_BIN --version

                                echo "Setting up virtual environment..."
                                rm -rf .mldenv || true
                                $PYTHON_BIN -m venv .mldenv
                                . .mldenv/bin/activate

                                echo "Upgrading pip and installing dependencies..."
                                pip install --upgrade pip
                                [ -f requirements.txt ] && pip install -r requirements.txt || echo "No requirements.txt found."

                                echo "Verifying AWS S3 access..."
                                aws s3 ls s3://mlflow1-remote || {
                                    echo "S3 access failed. Check AWS credentials."
                                    exit 1
                                }

                                echo "Running training script..."
                                python source/train.py
                            '''
                        } catch (Exception e) {
                            error "Setup stage failed: ${e.getMessage()}"
                        }
                    }
                }
            }
        }

        stage('Production Pipeline') {
            when { tag "release-*" }
            stages {
                stage('Deploy to Production') {
                    steps {
                        withCredentials([[
                            $class: 'AmazonWebServicesCredentialsBinding',
                            credentialsId: 'aws-credentials-id',
                            accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                            secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                        ]]) {
                            sh '''#!/bin/bash
                                set -x
                                . .mldenv/bin/activate
                                python source/deploy.py Challenger-post-test Production
                                
                                python -c "
import mlflow
client = mlflow.tracking.MlflowClient()
model_version = client.get_latest_versions('iris_model', stages=['Production'])[0].version
client.set_registered_model_alias('iris_model', 'Champion', model_version)
"
                            '''
                        }
                    }
                }
                
                stage('Deploy to MLflow Webserver') {
                    steps {
                        withCredentials([[
                            $class: 'AmazonWebServicesCredentialsBinding',
                            credentialsId: 'aws-credentials-id',
                            accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                            secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                        ]]) {
                            sh '''#!/bin/bash
                                set -x
                                . .mldenv/bin/activate

                                echo "Fetching latest production model..."
                                MODEL_VERSION=$(python -c "
import mlflow
client = mlflow.tracking.MlflowClient()
model_version = client.get_latest_versions('iris_model', stages=['Production'])[0].version
print(model_version)
")
                                
                                echo "Downloading the model from MLflow..."
                                mlflow artifacts download --artifact-uri "models:/iris_model/$MODEL_VERSION" --dst-path "./model"

                                echo "Starting MLflow Model Serving..."
                                nohup mlflow models serve -m "models:/iris_model/$MODEL_VERSION" --port 5001 --host 0.0.0.0 --no-conda > mlflow.log 2>&1 &
                                
                                echo "MLflow model is being served on http://localhost:5001"
                            '''
                        }
                    }
                }
                
                stage('Notify') {
                    steps {
                        notifyEmail('Production Pipeline Complete with MLflow Deployment')
                    }
                }
            }
        }
    }

    post {
        always {
            sh 'rm -rf .mldenv || true'
        }
        failure {
            notifyEmail('Pipeline Failed')
        }
    }
}
