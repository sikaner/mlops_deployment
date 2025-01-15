@Library('jenkins-shared-library') _

pipeline {
    agent any
    
    environment {
        MLFLOW_TRACKING_URI = 'http://localhost:5000'
        VIRTUAL_ENV = "/var/lib/jenkins/workspace/mlflow_dep_dev/mldenv"
        PATH = "${VIRTUAL_ENV}/bin:${PATH}"
    }

    stages {
        stage('Setup') {
            steps {  
                sh '''
                    sudo chown -R jenkins:jenkins ${VIRTUAL_ENV}
                    sudo chmod -R 755 ${VIRTUAL_ENV}
            
                    #!/bin/bash
                    set -e  # Exit immediately if a command exits with a non-zero status

                    # Use an explicit Python path
                    PYTHON_BIN=$(which python3)
                    if [ -z "$PYTHON_BIN" ]; then
                        echo "Python not found. Ensure Python is installed and accessible."
                        exit 1
                    fi

                    # Verify Python is executable
                    $PYTHON_BIN --version

                    # Create a virtual environment
                    $PYTHON_BIN -m venv mldenv

                    # Activate the virtual environment
                    source mldenv/bin/activate

                    # Install dependencies if requirements.txt exists
                    if [ -f requirements.txt ]; then
                        pip install -r requirements.txt
                    fi
                '''
            }
        }

        stage('Development Pipeline') {
            when {
                branch 'dev'
            }
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
            when {
                branch 'main'
            }
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
                            sh '''
                                #!/bin/bash
                                set -e
                                source mldenv/bin/activate
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
                        script {
                            deployModel('Challenger-post-test', 'Production')
                            sh '''
                                #!/bin/bash
                                set -e
                                source mldenv/bin/activate
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
    }
}
