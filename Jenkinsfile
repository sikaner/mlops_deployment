@Library('jenkins-shared-library') _

pipeline {
    agent any
    
    environment {
        MLFLOW_TRACKING_URI = 'http://localhost:5000'
        VIRTUAL_ENV = "${WORKSPACE}/.mldenv"
        PATH = "${VIRTUAL_ENV}/bin:${PATH}"
        AWS_DEFAULT_REGION = 'us-east-1'  
        RUN_ID = '7cb7836bab814dc397fca997f2d4a2cb'  // Your MLflow run ID
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
                                set -x  # Print each command before execution
                                
                                # Check if Python is installed
                                PYTHON_BIN=$(which python3 || true)
                                if [ -z "$PYTHON_BIN" ]; then
                                    echo "Python not found. Ensure Python is installed."
                                    exit 1
                                fi
                                $PYTHON_BIN --version

                                # Set up virtual environment and install dependencies
                                rm -rf .mldenv || true
                                $PYTHON_BIN -m venv .mldenv
                                . .mldenv/bin/activate
                                pip install --upgrade pip
                                [ -f requirements.txt ] && pip install -r requirements.txt || echo "No requirements.txt found."

                                # Install additional dependencies for serving model
                                pip install mlflow boto3
                            '''
                        } catch (Exception e) {
                            error "Setup stage failed: ${e.getMessage()}"
                        }
                    }
                }
            }
        }

        stage('Deploy Model to MLflow') {
            steps {
                withCredentials([[ 
                    $class: 'AmazonWebServicesCredentialsBinding', 
                    credentialsId: 'aws-credentials-id', 
                    accessKeyVariable: 'AWS_ACCESS_KEY_ID', 
                    secretKeyVariable: 'AWS_SECRET_ACCESS_KEY' 
                ]]) {
                    sh '''#!/bin/bash
                        set -e
                        set -x
                        . .mldenv/bin/activate

                        # Kill any existing MLflow processes
                        pkill -f "mlflow models serve" || true
                        sleep 5

                        # Start MLflow model server
                        nohup mlflow models serve -m "runs:/${RUN_ID}/model" \
                            --host 0.0.0.0 \
                            --port 5001 \
                            --no-conda \
                            > mlflow_serve.log 2>&1 &

                        # Wait for the server to start
                        echo "Waiting for MLflow server to start..."
                        sleep 20

                        # Test the deployment
                        if curl -s -f http://localhost:5001/health; then
                            echo "MLflow model server is running successfully"
                        else
                            echo "MLflow model server failed to start. Checking logs:"
                            cat mlflow_serve.log
                            exit 1
                        fi
                    '''
                }
            }
        }

        stage('Verify Deployment') {
            steps {
                sh '''#!/bin/bash
                    set -e
                    set -x
                    . .mldenv/bin/activate

                    # Test prediction endpoint with sample data
                    curl -X POST -H "Content-Type:application/json" \
                        --data '{"dataframe_split": {"columns":["petal length (cm)", "petal width (cm)", "sepal length (cm)", "sepal width (cm)"], "data":[[5.1, 3.5, 1.4, 0.2]]}}' \
                        http://localhost:5001/invocations
                '''
            }
        }

        stage('Notify') {
            steps {
                notifyEmail('Model Deployment Complete')
            }
        }
    }
    
    post {
        always {
            sh '''#!/bin/bash
                # Cleanup
                if [ -d ".mldenv" ]; then
                    rm -rf .mldenv
                fi

                # Save MLflow logs before cleanup
                if [ -f mlflow_serve.log ]; then
                    cp mlflow_serve.log ${WORKSPACE}/mlflow_serve_${BUILD_NUMBER}.log
                fi
            '''
        }
        failure {
            notifyEmail('Pipeline Failed')
        }
    }
}
