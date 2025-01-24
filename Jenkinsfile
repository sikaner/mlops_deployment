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
        stage('Conditional Pipeline') {
            stages {
                // Development Branch Pipeline
                stage('Development Pipeline') {
                    when { branch 'dev' }
                    stages {
                        stage('Setup Dev Environment') {
                            steps {
                                script {
                                    withAWS(credentials: 'aws-credentials-id', region: 'us-east-1') {
                                        sh '''#!/bin/bash
                                            set -e
                                            if [ ! -d ".mldenv" ]; then
                                                python3 -m venv .mldenv
                                                . .mldenv/bin/activate
                                                python3 -m ensurepip
                                                pip install --upgrade pip
                                                pip install -r requirements.txt
                                            fi
                                        '''
                                    }
                                }
                            }
                        }

                        stage('Train Model') {
                            steps {
                                script {
                                    withAWS(credentials: 'aws-credentials-id', region: 'us-east-1') {
                                        sh '''#!/bin/bash
                                            set -e
                                            . .mldenv/bin/activate
                                            python source/train.py
                                        '''
                                    }
                                }
                            }
                        }

                        stage('Run Tests') {
                            steps {
                                script {
                                    withAWS(credentials: 'aws-credentials-id', region: 'us-east-1') {
                                        sh '''#!/bin/bash
                                            set -e
                                            . .mldenv/bin/activate
                                            python source/test.py Challenger
                                        '''
                                    }
                                }
                            }
                        }

                        stage('Deploy to Dev') {
                            steps {
                                script {
                                    withAWS(credentials: 'aws-credentials-id', region: 'us-east-1') {
                                        sh '''#!/bin/bash
                                            set -e
                                            . .mldenv/bin/activate
                                            python source/deploy.py Challenger Staging
                                        '''
                                    }
                                }
                            }
                        }

                        stage('Notify Dev Complete') {
                            steps {
                                script {
                                    notifyEmail('Development Pipeline Complete')
                                }
                            }
                        }
                    }
                }

                // Main Branch (Pre-Production) Pipeline
                stage('Pre-Production Pipeline') {
                    when { branch 'main' }
                    stages {
                        stage('Validate Staging Model') {
                            steps {
                                script {
                                    withAWS(credentials: 'aws-credentials-id', region: 'us-east-1') {
                                        sh '''#!/bin/bash
                                            set -e
                                            . .mldenv/bin/activate
                                            python source/test.py Challenger
                                        '''
                                    }
                                }
                            }
                        }

                        stage('Update Model Alias') {
                            steps {
                                script {
                                    withAWS(credentials: 'aws-credentials-id', region: 'us-east-1') {
                                        sh '''#!/bin/bash
                                            set -e
                                            . .mldenv/bin/activate
                                            python source/deploy.py Challenger Staging
                                            python -c "
import mlflow
try:
    client = mlflow.tracking.MlflowClient()
    model_version = client.get_latest_versions('iris_model', stages=['Staging'])[0].version
    client.set_registered_model_alias('iris_model', 'Challenger-post-test', model_version)
except Exception as e:
    print(f'Error updating model alias: {e}')
"
                                        '''
                                    }
                                }
                            }
                        }

                        stage('Notify Pre-Prod Complete') {
                            steps {
                                script {
                                    notifyEmail('Pre-Production Pipeline Complete')
                                }
                            }
                        }
                    }
                }

                // Production Release Pipeline
                stage('Production Release Pipeline') {
                    when { expression { env.GIT_TAG == 'v1.0.1' } }
                    stages {
                        stage('Deploy to Production') {
                            steps {
                                script {
                                    withAWS(credentials: 'aws-credentials-id', region: 'us-east-1') {
                                        sh '''#!/bin/bash
                                            set -e
                                            . .mldenv/bin/activate
                                            python source/deploy.py Challenger-post-test Production
                                            python -c "
import mlflow
try:
    client = mlflow.tracking.MlflowClient()
    model_version = client.get_latest_versions('iris_model', stages=['Production'])[0].version
    client.set_registered_model_alias('iris_model', 'Champion', model_version)
except Exception as e:
    print(f'Error updating model alias: {e}')
"
                                        '''
                                    }
                                }
                            }
                        }

                        stage('Notify Production Release') {
                            steps {
                                script {
                                    notifyEmail('Production Release Deployed')
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                sh 'rm -rf .mldenv || true'
            }
        }
        failure {
            script {
                notifyEmail('Pipeline Execution Failed')
            }
        }
    }
}

//abc233