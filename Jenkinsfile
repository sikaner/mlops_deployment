@Library('jenkins-shared-library') _

pipeline {
    agent any

    environment {
        MLFLOW_TRACKING_URI = 'http://localhost:5000'
        VIRTUAL_ENV = "${WORKSPACE}/.mldenv"
        PATH = "${VIRTUAL_ENV}/bin:${PATH}"
        AWS_DEFAULT_REGION = 'us-east-1'
    }

    stages {
        stage('Setup') {
            steps {
                withAWS(credentials: 'aws-credentials-id', region: 'us-east-1') {
                    script {
                        try {
                            sh '''#!/bin/bash
                                set -e
                                set -x  # Print each command before execution

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

                                echo "Checking AWS credentials..."
                                aws sts get-caller-identity || { echo "AWS credentials missing!"; exit 1; }

                                echo "Verifying AWS S3 access..."
                                aws s3 ls s3://mlflow1-remote || { echo "S3 access failed. Check AWS credentials."; exit 1; }

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

        stage('Development Pipeline') {
            when { expression { env.BRANCH_NAME == 'dev' } }
            stages {
                stage('Train') {
                    steps {
                        withAWS(credentials: 'aws-credentials-id', region: 'us-east-1') {
                            sh '''
                                set -x
                                . .mldenv/bin/activate
                                export AWS_PROFILE=default
                                export AWS_SHARED_CREDENTIALS_FILE=$HOME/.aws/credentials
                                python source/train.py
                            '''
                        }
                    }
                }
                stage('Test') {
                    steps {
                        withAWS(credentials: 'aws-credentials-id', region: 'us-east-1') {
                            sh '''
                                set -x
                                . .mldenv/bin/activate
                                python source/test.py Challenger
                            '''
                        }
                    }
                }
                stage('Deploy to Dev') {
                    steps {
                        withAWS(credentials: 'aws-credentials-id', region: 'us-east-1') {
                            sh '''
                                set -x
                                . .mldenv/bin/activate
                                python source/deploy.py Challenger Staging
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
            when { expression { env.BRANCH_NAME == 'main' } }
            stages {
                stage('Load and Test') {
                    steps {
                        withAWS(credentials: 'aws-credentials-id', region: 'us-east-1') {
                            sh '''
                                set -x
                                . .mldenv/bin/activate
                                python source/test.py Challenger
                            '''
                        }
                    }
                }
                stage('Update Alias') {
                    steps {
                        withAWS(credentials: 'aws-credentials-id', region: 'us-east-1') {
                            sh '''
                                set -x
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
            when { expression { env.GIT_BRANCH.startsWith('refs/tags/release-') } }
            stages {
                stage('Deploy to Production') {
                    steps {
                        withAWS(credentials: 'aws-credentials-id', region: 'us-east-1') {
                            sh '''
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
