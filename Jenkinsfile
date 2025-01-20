@Library('jenkins-shared-library') _

pipeline {
    agent any
    
    environment {
        MLFLOW_TRACKING_URI = 'http://127.0.0.1:5000'  // Corrected MLFLOW_TRACKING_URI for local environment
        VIRTUAL_ENV = "${WORKSPACE}/.mldenv"
        PATH = "${VIRTUAL_ENV}/bin:${PATH}"
        AWS_DEFAULT_REGION = 'us-east-1'  
        RUN_ID = 'cb1e5b0e4eb945fd8c4cf5466c35eb09'  // Your MLflow run ID
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
                                
                                # Ensure MLFLOW_TRACKING_URI is set
                                export MLFLOW_TRACKING_URI=http://127.0.0.1:5000

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
                    script {
                        try {
                            sh '''#!/bin/bash
                                set -e
                                set -x
                                . .mldenv/bin/activate

                                # Check if tmux session exists, and kill it if necessary
                                if tmux ls | grep -q 'mlflow_server'; then
                                    tmux kill-session -t mlflow_server
                                fi

                                # Start a new tmux session
                                tmux new-session -d -s mlflow_server "mlflow models serve -m 'runs:/cb1e5b0e4eb945fd8c4cf5466c35eb09/model' --host 0.0.0.0 --port 5002 --no-conda"
                                
                                # Give it some time to start the server
                                sleep 10

                                # Test the deployment by checking server health
                                if curl -s -f http://127.0.0.1:5002/health; then
                                    echo "MLflow model server is running successfully"
                                else
                                    echo "MLflow model server failed to start. Checking logs:"
                                    cat mlflow_serve.log
                                    exit 1
                                fi
                            '''
                        } catch (Exception e) {
                            error "Deployment failed: ${e.getMessage()}"
                        }
                    }
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
                        --data '{"dataframe_split": {"columns":["sepal length (cm)", "sepal width (cm)", "petal length (cm)", "petal width (cm)"], "data":[[5.1, 3.5, 1.4, 0.2]]}}' \
                        http://127.0.0.1:5002/invocations
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
