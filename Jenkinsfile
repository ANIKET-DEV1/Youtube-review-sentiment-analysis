pipeline {
    agent any

    environment {
        PYTHONUNBUFFERED = '1'
        PYTHONPATH = '.'
    }

    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Set Up Python Environment') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    if [ -f requirements.txt ]; then
                        pip install -r requirements.txt
                    fi
                '''
            }
        }

        stage('Train Model') {
            steps {
                sh '''
                    . .venv/bin/activate
                    python ml/train.py
                '''
            }
        }

        stage('Evaluate Performance Gate') {
            steps {
                sh '''
                    . .venv/bin/activate
                    python ml/evaluate.py
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    . .venv/bin/activate
                    pytest -v tests/test_api.py
                '''
            }
        }

        stage('Archive Model Artifact') {
            steps {
                archiveArtifacts artifacts: 'models/*.pkl', fingerprint: true, allowEmptyArchive: false
            }
        }

        stage('Build & Test Docker Container') {
            steps {
                sh '''
                    # Stop previous container if still alive
                    docker rm -f api-test-container 2>/dev/null || true

                    # Build image from root Dockerfile
                    docker build -t yt-sentiment-app:latest .

                    # Run container locally
                    docker run -d --name api-test-container yt-sentiment-app:latest

                    # Obtain internal IP to verify endpoint
                    CONTAINER_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' api-test-container)

                    timeout 30 bash -c "until curl -s -f http://${CONTAINER_IP}:8000/health; do sleep 2; done" || {
                        echo "Health check failed. Container output:"
                        docker logs api-test-container
                        docker rm -f api-test-container
                        exit 1
                    }

                    echo "Container health check passed."
                '''
            }
        }
    }

    post {
        always {
            sh 'docker rm -f api-test-container 2>/dev/null || true'
        }
    }
}