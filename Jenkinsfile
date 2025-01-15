@Library('jenkins-shared-library') _

pipeline {
    agent any
    
    environment {
        MLFLOW_TRACKING_URI = 'http://localhost:5000'
        VIRTUAL_ENV = "${WORKSPACE}/mldenv"
        PATH = "${VIRTUAL_ENV}/bin:${PATH}"
        PYTHON_CMD = "python3"
    }
    
    stages {
        stage('Setup') {
            steps {
                // Clean and setup virtual environment without sudo
                sh '''#!/bin/bash -l
                    # Remove existing venv if present
                    rm -rf mldenv
                    
                    # Create new venv
                    ${PYTHON_CMD} -m venv mldenv
                    
                    # Activate virtual environment
                    . mldenv/bin/activate
                    
                    # Install requirements
                    python -m pip install --upgrade pip --user
                    pip install -r requirements.txt --user
                '''
            }
        }
        
        stage('Development Pipeline') {
            when { branch 'dev' }
            stages {
                stage('Train') {
                    steps {
                        trainModel()
                    }
                }
                stage('Test') {
                    steps {
                        testModel('Challenger')
                    }
                }
                stage('Deploy to Dev') {
                    steps {
                        deployModel('Challenger', 'Development')
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
                        testModel('Challenger')
                    }
                }
                stage('Update Alias') {
                    steps {
                        deployModel('Challenger', 'Staging')
                        script {
                            sh '''#!/bin/bash -l
                                . mldenv/bin/activate
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
                        script {
                            deployModel('Challenger-post-test', 'Production')
                            sh '''#!/bin/bash -l
                                . mldenv/bin/activate
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
        failure {
            notifyEmail('Pipeline Failed')
        }
        cleanup {
            cleanWs()
        }
    }
}