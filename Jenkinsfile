@Library('jenkins-shared-library') _

pipeline {
    agent any
    
    environment {
        MLFLOW_TRACKING_URI = 'http://localhost:5000'
        VIRTUAL_ENV = "${WORKSPACE}/.mldenv"
        PATH = "${VIRTUAL_ENV}/bin:${PATH}"
        AWS_DEFAULT_REGION = 'us-east-1'
        // Add MLflow server credentials
        MLFLOW_TRACKING_USERNAME = credentials('mlflow-username')
        MLFLOW_TRACKING_PASSWORD = credentials('mlflow-password')  
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

                                echo "Verifying MLflow server access..."
                                curl -u ${MLFLOW_TRACKING_USERNAME}:${MLFLOW_TRACKING_PASSWORD} ${MLFLOW_TRACKING_URI}/api/2.0/mlflow/experiments/list || {
                                    echo "MLflow server access failed. Check credentials."
                                    exit 1
                                }
                            '''
                        } catch (Exception e) {
                            error "Setup stage failed: ${e.getMessage()}"
                        }
                    }
                }
            }
        }

        stage('Development Pipeline') {
            stages {
                stage('Train') {
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
                                python source/train.py
                            '''
                        }
                    }
                }
                stage('Test') {
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
                                python source/test.py Challenger
                            '''
                        }
                    }
                }
                stage('Deploy to MLflow') {
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
                                
                                # Deploy to MLflow server
                                mlflow models serve -m "models:/iris_model/Staging" \
                                    --host 0.0.0.0 \
                                    --port 5001 \
                                    --enable-mlserver \
                                    --workers 3 &
                                
                                # Wait for server to start
                                sleep 10
                                
                                # Verify deployment
                                curl -X GET http://localhost:5001/health | grep "ok" || {
                                    echo "MLflow model server deployment failed"
                                    exit 1
                                }
                            '''
                        }
                    }
                }
                stage('Notify') {
                    steps {
                        notifyEmail('Development Pipeline Complete')
                    }
                }
            }
        }

        stage('Production Pipeline') {
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
                                
                                # Update model to Production stage
                                python source/deploy.py Challenger-post-test Production
                                
                                # Update Champion alias
                                python -c "
import mlflow
client = mlflow.tracking.MlflowClient()
model_version = client.get_latest_versions('iris_model', stages=['Production'])[0].version
client.set_registered_model_alias('iris_model', 'Champion', model_version)
"

                                # Deploy Production model to MLflow server
                                mlflow models serve -m "models:/iris_model/Production" \
                                    --host 0.0.0.0 \
                                    --port 5002 \
                                    --enable-mlserver \
                                    --workers 5 &
                                
                                # Wait for server to start
                                sleep 10
                                
                                # Verify deployment
                                curl -X GET http://localhost:5002/health | grep "ok" || {
                                    echo "Production model server deployment failed"
                                    exit 1
                                }
                            '''
                        }
                    }
                }
                stage('Notify') {
                    steps {
                        notifyEmail('Production Pipeline Complete')
                    }
                }
            }
        }
    }
    
    post {
        always {
            sh '''
                # Stop MLflow model servers
                pkill -f "mlflow models serve" || true
                rm -rf .mldenv || true
            '''
        }
        failure {
            notifyEmail('Pipeline Failed')
        }
    }
}