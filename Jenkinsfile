pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build') {
            when {
                branch 'dev'
            }
            steps {
                echo 'Building for dev branch...'
                // Add build steps here
            }
        }

        stage('Test') {
            when {
                branch 'dev'
            }
            steps {
                echo 'Testing on dev branch...'
                // Add test steps here
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                echo 'Deploying main branch...'
                // Add deployment steps here
            }
        }

        stage('Release Tag') {
            when {
                branch 'main'
            }
            steps {
                script {
                    def commitHash = sh(returnStdout: true, script: 'git rev-parse HEAD').trim()
                    def tagName = "release-${env.BUILD_NUMBER}"
                    sh "git tag -a ${tagName} -m 'Release tag for build ${env.BUILD_NUMBER}' ${commitHash}"
                    sh "git push origin ${tagName}"
                    echo "Tag ${tagName} created and pushed."
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline execution completed!'
        }
    }
}
