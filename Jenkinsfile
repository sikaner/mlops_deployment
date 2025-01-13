@Library('jenkins-shared-library') _

pipeline {
    agent any
    
    environment {
        MLFLOW_TRACKING_URI = 'http://localhost:5000'
    }
    
    stages {
        stage('Determine Environment') {
            steps {
                script {
                    if (env.BRANCH_NAME == 'dev') {
                        env.DEPLOY_ENV = 'dev'
                    } else if (env.BRANCH_NAME == 'main') {
                        env.DEPLOY_ENV = 'preprod'
                    } else if (env.TAG_NAME) {
                        env.DEPLOY_ENV = 'prod'
                    } else {
                        error "Unknown branch/tag"
                    }
                }
            }
        }
        
        stage('Train Model') {
            when { 
                expression { env.DEPLOY_ENV == 'dev' }
            }
            steps {
                script {
                    try {
                        modelTrain()
                    } catch (Exception e) {
                        currentBuild.result = 'FAILURE'
                        emailNotification('FAILED', env.DEPLOY_ENV)
                        error "Model training failed: ${e.getMessage()}"
                    }
                }
            }
        }
        
        stage('Test Model') {
            when {
                expression { env.DEPLOY_ENV in ['dev', 'preprod'] }
            }
            steps {
                script {
                    try {
                        modelTest(env.DEPLOY_ENV)
                    } catch (Exception e) {
                        currentBuild.result = 'FAILURE'
                        emailNotification('FAILED', env.DEPLOY_ENV)
                        error "Model testing failed: ${e.getMessage()}"
                    }
                }
            }
        }
        
        stage('Deploy Model') {
            steps {
                script {
                    try {
                        modelDeploy(env.DEPLOY_ENV)
                        emailNotification('SUCCESS', env.DEPLOY_ENV)
                    } catch (Exception e) {
                        currentBuild.result = 'FAILURE'
                        emailNotification('FAILED', env.DEPLOY_ENV)
                        error "Model deployment failed: ${e.getMessage()}"
                    }
                }
            }
        }
    }
}