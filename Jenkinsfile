@Library('jenkins-shared-library') _

pipeline {
    agent any
    
    environment {
        MLFLOW_TRACKING_URI = 'http://localhost:5000'
        VIRTUAL_ENV = "${WORKSPACE}/.mldenv"
        PATH = "${VIRTUAL_ENV}/bin:${PATH}"
        // Add AWS credentials environment variables
        AWS_DEFAULT_REGION = 'us-east-1'  // Replace with your AWS region
    }

    stages {
        stage('Setup') {
            steps {
                // Wrap the entire setup in withCredentials block
                withCredentials([[
                    $class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: 'aws-credentials-id',
                    accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                    secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                ]]) {
                    sh '''#!/bin/bash
                        # Exit on any error
                        set -e

                        # Use explicit Python path
                        PYTHON_BIN=$(which python3)
                        if [ -z "$PYTHON_BIN" ]; then
                            echo "Python not found. Ensure Python is installed and accessible."
                            exit 1
                        fi

                        # Verify Python is executable
                        $PYTHON_BIN --version

                        # Remove existing virtual environment if it exists
                        rm -rf .mldenv || true

                        # Create virtual environment
                        $PYTHON_BIN -m venv .mldenv

                        # Use . instead of source for shell compatibility
                        . .mldenv/bin/activate || {
                            echo "Failed to activate virtual environment"
                            exit 1
                        }

                        # Upgrade pip and install requirements
                        pip install --upgrade pip
                        if [ -f requirements.txt ]; then
                            pip install -r requirements.txt
                        fi

                        # Test S3 access (aws s3 ls should work with valid credentials)
                        aws s3 ls s3://mlflow1-remote
                    '''
                }
            }
        }

        stage('Development Pipeline') {
            when {
                branch 'dev'
            }
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
            when {
                branch 'main'
            }
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
            when {
                tag "release-*" 
            }
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
            // Cleanup
            sh 'rm -rf .mldenv || true'
        }
        failure {
            notifyEmail('Pipeline Failed')
        }
    }
}
