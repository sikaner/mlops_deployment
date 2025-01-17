@Library('jenkins-shared-library') _

pipeline {
    agent any  // This specifies to run on any available agent
    
    environment {
        MLFLOW_TRACKING_URI = 'http://localhost:5000'
        VIRTUAL_ENV = "${WORKSPACE}/.mldenv"
        PATH = "${VIRTUAL_ENV}/bin:${PATH}"
        AWS_DEFAULT_REGION = 'us-east-1'
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

                stage('Deploy Model') {
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
                                python source/deploy.py Challenger Staging
                                
                                # Start MLflow model server
                                mlflow models serve -m "models:/iris_model/Staging" \
                                    --host 0.0.0.0 \
                                    --port 5001 \
                                    --workers 3 &
                                
                                # Wait for server to start
                                sleep 10
                                
                                # Verify deployment
                                curl -X GET http://localhost:5001/health || {
                                    echo "MLflow model server deployment failed"
                                    exit 1
                                }
                            '''
                        }
                    }
                }
                
                stage('Notify') {
                    steps {
                        script {
                            emailext (
                                subject: 'Development Pipeline Complete',
                                body: 'The development pipeline has completed successfully.',
                                to: 'your-email@example.com',
                                from: 'jenkins@your-domain.com'
                            )
                        }
                    }
                }
            }
        }
    }
    
    post {
        always {
            sh '''#!/bin/bash
                # Stop MLflow model servers if running
                pkill -f "mlflow models serve" || true
                
                # Clean up virtual environment
                if [ -d ".mldenv" ]; then
                    rm -rf .mldenv
                fi
            '''
        }
        failure {
            script {
                emailext (
                    subject: 'Pipeline Failed',
                    body: 'The pipeline has failed. Please check Jenkins for details.',
                    to: 'your-email@example.com',
                    from: 'jenkins@your-domain.com'
                )
            }
        }
    }
}