pipeline {
    agent any

    options {
        timeout(time: 20, unit: 'MINUTES')
    }

    stages {
        stage('Check tools') {
            steps {
                sh 'python3 --version'
            }
        }

        stage('Create venv') {
            steps {
                sh 'python3 -m venv .venv'
            }
        }

        stage('Install dependencies') {
            steps {
                sh '. .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt'
            }
        }
    }
}