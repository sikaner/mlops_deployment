@Library('jenkins-shared-library') _

pipeline {
    agent any

    environment {
        MLFLOW_TRACKING_URI = 'http://localhost:5000'
        VIRTUAL_ENV = "${WORKSPACE}/.mldenv"
        PATH = "${VIRTUAL_ENV}/bin:${PATH}"
        AWS_DEFAULT_REGION = 'us-east-1'  // Ensure AWS region is set
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
                                set -e  # Exit on failure
                                set -x  # Show executed commands

                                echo "Checking Python installation..."
                                PYTHON_BIN=$(which python3 || true)
                                if [ -z "$PYTHON_BIN" ]; then
                                    echo "ERROR: Python not found. Ensure Python is installed."
                                    exit 1
                                fi
                                $PYTHON_BIN --version

                                echo "Setting up virtual environment..."
                                rm -rf .mldenv || true
                                $PYTHON_BIN -m venv .mldenv || { echo "ERROR: Failed to create virtual environment."; exit 1; }
                                . .mldenv/bin/activate || { echo "ERROR: Failed to activate virtual environment."; exit 1; }

                                echo "Upgrading pip..."
                                pip install --upgrade pip || { echo "ERROR: Failed to upgrade pip."; exit 1; }

                                echo "Installing dependencies from requirements.txt..."
                                if [ -f requirements.txt ]; then
                                    pip install -r requirements.txt || { echo "ERROR: Failed to install dependencies."; exit 1; }
                                else
                                    echo "WARNING: requirements.txt not found. Skipping dependency installation."
                                fi

                                echo "Verifying AWS CLI installation..."
                                if ! command -v aws &> /dev/null; then
                                    echo "ERROR: AWS CLI is not installed."
                                    exit 1
                                fi
                                aws --version

                                echo "Checking AWS S3 access..."
                                aws s3 ls s3://mlflow1-remote || { echo "ERROR: S3 access failed. Check AWS credentials."; exit 1; }

                                echo "Running training script..."
                                python source/train.py || { echo "ERROR: Training script execution failed."; exit 1; }

                                echo "Setup stage completed successfully!"
                            '''
                        } catch (Exception e) {
                            error "Setup stage failed: ${e.getMessage()}"
                        }
                    }
                }
            }
        }

        stage('Development Pipeline') {
            when { branch 'dev' }
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
                                . .mldenv/bin/activate
                                python source/test.py Challenger
                            '''
                        }
                    }
                }
                stage('Deploy to Dev') {
                    steps {
                        withCredentials([[
                            $class: 'AmazonWebServicesCredentialsBinding',
                            credentialsId: 'aws-credentials-id',
                            accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                            secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                        ]]) {
                            sh '''#!/bin/bash
                                . .mldenv/bin/activate
                                python source/deploy.py Challenger Development
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

        stage('Pre-prod Pipeline') {
            when { branch 'main' }
            stages {
                stage('Load and Test') {
                    steps {
                        withCredentials([[
                            $class: 'AmazonWebServicesCredentialsBinding',
                            credentialsId: 'aws-credentials-id',
                            accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                            secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                        ]]) {
                            sh '''#!/bin/bash
                                . .mldenv/bin/activate
                                python source/test.py Challenger
                            '''
                        }
                    }
                }
                stage('Update Alias') {
                    steps {
                        withCredentials([[
                            $class: 'AmazonWebServicesCredentialsBinding',
                            credentialsId: 'aws-credentials-id',
                            accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                            secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                        ]]) {
                            sh '''#!/bin/bash
                                . .mldenv/bin/activate
                                python source/deploy.py Challenger Staging

                                python -c "
import mlflow
client = mlflow.tracking.MlflowClient()
model_version = client.get_latest_versions('iris_model', stages=['Staging'])[0].version
client.set_registered_model_alias('iris_model', 'Challenger-post-test', model_version)
"
                            '''
                        }
                    }
                }
                stage('Notify') {
                    steps {
                        notifyEmail('Pre-production Pipeline Complete')
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
            sh 'rm -rf .mldenv || true'
        }
        failure {
            notifyEmail('Pipeline Failed')
        }
    }
}
