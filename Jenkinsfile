pipeline {
    agent any

    stages {
        stage('Show repo') {
            steps {
                sh 'echo "Build number: $BUILD_NUMBER"'
                sh 'git log -1 --oneline'
                sh 'ls -la'
            }
        }

        stage('Check tools') {
            steps {
                sh 'python3 --version || echo "python3 is NOT installed in this Jenkins container"'
            }
        }
    }
}