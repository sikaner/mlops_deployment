@Library('jenkins-shared-library') _

pipeline {
    agent any
    
    environment {
        MLFLOW_TRACKING_URI = 'http://127.0.0.1:5000'
        VIRTUAL_ENV = "${WORKSPACE}/.mldenv"
        PATH = "${HOME}/.pyenv/bin:${HOME}/.pyenv/shims:${VIRTUAL_ENV}/bin:${PATH}"
        AWS_DEFAULT_REGION = 'us-east-1'
        RUN_ID = '7cb7836bab814dc397fca997f2d4a2cb'  // Your MLflow run ID
    }

    stages {
        stage('Setup Environment') {
            steps {
                withCredentials([[
                    $class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: 'aws-credentials-id',
                    accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                    secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                ]]) {
                    sh '''#!/bin/bash
                        set -e
                        
                        # Ensure pyenv is installed and initialized
                        if ! command -v pyenv &> /dev/null; then
                            echo "pyenv not found. Installing..."
                            curl https://pyenv.run | bash
                        fi
                        
                        # Initialize pyenv
                        export PATH="$HOME/.pyenv/bin:$PATH"
                        eval "$(pyenv init --path)"
                        eval "$(pyenv init -)"
                        eval "$(pyenv virtualenv-init -)"
                        
                        # Create and activate virtual environment
                        python3 -m pip install --user virtualenv
                        python3 -m virtualenv ${VIRTUAL_ENV}
                        source ${VIRTUAL_ENV}/bin/activate
                        
                        # Install required packages
                        pip install --upgrade pip
                        pip install mlflow boto3 scikit-learn pandas
                        
                        # Verify MLflow installation
                        mlflow --version
                    '''
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
                        source ${VIRTUAL_ENV}/bin/activate
                        
                        # Kill any existing MLflow processes
                        pkill -f "mlflow models serve" || true
                        sleep 5
                        
                        # Start MLflow model server
                        nohup mlflow models serve -m "runs:/${RUN_ID}/model" \
                            --host 0.0.0.0 \
                            --port 5001 \
                            --no-conda \
                            > mlflow_serve.log 2>&1 &
                        
                        # Wait for server to start
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
                    source ${VIRTUAL_ENV}/bin/activate
                    
                    # Test prediction endpoint with sample data
                    curl -X POST -H "Content-Type:application/json" \
                        --data '{"dataframe_split": {"columns":["feature1", "feature2", "feature3", "feature4"], "data":[[5.1, 3.5, 1.4, 0.2]]}}' \
                        http://localhost:5001/invocations
                '''
            }
        }
    }
    
    post {
        success {
            script {
                emailext(
                    subject: "Model Deployment Successful",
                    body: "MLflow model has been successfully deployed and is serving on port 5001",
                    to: "your-email@example.com"
                )
            }
        }
        failure {
            script {
                emailext(
                    subject: "Model Deployment Failed",
                    body: "MLflow model deployment failed. Please check Jenkins logs for details.",
                    to: "your-email@example.com"
                )
            }
        }
        always {
            sh '''#!/bin/bash
                # Cleanup
                if [ -d "${VIRTUAL_ENV}" ]; then
                    rm -rf ${VIRTUAL_ENV}
                fi
                
                # Save MLflow logs before cleanup
                if [ -f mlflow_serve.log ]; then
                    cp mlflow_serve.log ${WORKSPACE}/mlflow_serve_${BUILD_NUMBER}.log
                fi
            '''
        }
    }
}
