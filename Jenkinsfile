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
                echo 'Setting up environment...'
            }
        }

        stage('Development Pipeline') {
            when { branch 'dev' }
            stages {
                stage('Train') {
                    steps { echo 'Training model...' }
                }
                stage('Test') {
                    steps { echo 'Testing model...' }
                }
                stage('Deploy to Dev') {
                    steps { echo 'Deploying to Dev...' }
                }
                stage('Notify') {
                    steps { notifyEmail('Development Pipeline Complete') }
                }
            }
        }

        stage('Pre-prod Pipeline') {
            when { branch 'main' }
            stages {
                stage('Load and Test') {
                    steps { echo 'Testing pre-prod model...' }
                }
                stage('Update Alias') {
                    steps { echo 'Updating alias...' }
                }
                stage('Notify') {
                    steps { notifyEmail('Pre-production Pipeline Complete') }
                }
            }
        }

        stage('Production Pipeline') {
            when { expression { env.GIT_TAG_NAME?.startsWith('release-') } }
            stages {
                stage('Deploy to Production') {
                    steps { echo 'Deploying to Production...' }
                }
                stage('Notify') {
                    steps { notifyEmail('Production Pipeline Complete') }
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
