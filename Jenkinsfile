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
                withCredentials([[ // AWS credentials binding
                    $class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: 'aws-credentials-id',
                    accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                    secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                ]]) {
                    script {
                        try {
                            sh '''
                                set -e
                                echo "Setting up virtual environment..."
                                python3 -m venv .mldenv
                                . .mldenv/bin/activate
                                pip install --upgrade pip
                                [ -f requirements.txt ] && pip install -r requirements.txt || echo "No requirements.txt found."
                            '''
                        } catch (Exception e) {
                            error "Setup failed: ${e.getMessage()}"
                        }
                    }
                }
            }
        }

        stage('Development Pipeline') {
            when { branch 'dev' }
            stages {
                stage('Train') { /* Train model */ }
                stage('Test') { /* Test model */ }
                stage('Deploy to Dev') { /* Deploy to Dev */ }
                stage('Notify') { steps { notifyEmail('Development Pipeline Complete') } }
            }
        }

        stage('Pre-prod Pipeline') {
            when { branch 'main' }
            stages {
                stage('Load and Test') { /* Test pre-prod model */ }
                stage('Update Alias') { /* Update alias */ }
                stage('Notify') { steps { notifyEmail('Pre-production Pipeline Complete') } }
            }
        }

        stage('Production Pipeline') {
            when { expression { env.GIT_TAG_NAME?.startsWith('release-') } }
            stages {
                stage('Deploy to Production') {
                    steps {
                        withCredentials([[ // AWS credentials binding
                            $class: 'AmazonWebServicesCredentialsBinding',
                            credentialsId: 'aws-credentials-id',
                            accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                            secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                        ]]) {
                            sh '''
                                set -e
                                echo "Deploying to production..."
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
                stage('Notify') { steps { notifyEmail('Production Pipeline Complete') } }
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
