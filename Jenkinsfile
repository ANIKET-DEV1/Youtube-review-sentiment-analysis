pipeline {
    agent any

    // Auto-trigger: check GitHub every 2 minutes and build if there is a new commit.
    // For instant triggers, replace with: githubPush()  (needs a GitHub webhook + public URL)
    triggers {
        pollSCM('H/2 * * * *')
    }

    options {
        timeout(time: 45, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
        disableConcurrentBuilds()
    }

    environment {
        PYTHONUNBUFFERED = '1'
        PYTHONPATH = '.'
        IMAGE_NAME = 'yt-sentiment-app'
        TEST_CONTAINER = 'api-test-container'
        APP_CONTAINER = 'yt-sentiment-app'
        APP_PORT = '8000'
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
                    pip install --default-timeout=120 --retries 10 --upgrade pip
                    if [ -f requirements.txt ]; then
                        pip install --default-timeout=120 --retries 10 -r requirements.txt
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

        stage('Build Docker Image') {
            steps {
                // Retry handles flaky network during base image pull / pip install
                retry(3) {
                    sh '''
                        docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} -t ${IMAGE_NAME}:latest .
                    '''
                }
            }
        }

        stage('Test Container') {
            steps {
                sh '''
                    docker rm -f ${TEST_CONTAINER} 2>/dev/null || true

                    docker run -d --name ${TEST_CONTAINER} ${IMAGE_NAME}:${BUILD_NUMBER}

                    CONTAINER_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ${TEST_CONTAINER})

                    timeout 60 bash -c "until curl -s -f http://${CONTAINER_IP}:${APP_PORT}/health; do sleep 2; done" || {
                        echo "Health check failed. Container output:"
                        docker logs ${TEST_CONTAINER}
                        exit 1
                    }

                    echo "Test container is healthy."
                '''
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    docker rm -f ${APP_CONTAINER} 2>/dev/null || true

                    docker run -d --name ${APP_CONTAINER} \
                        --restart unless-stopped \
                        -p ${APP_PORT}:${APP_PORT} \
                        ${IMAGE_NAME}:${BUILD_NUMBER}

                    sleep 5
                    DEPLOY_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ${APP_CONTAINER})

                    timeout 60 bash -c "until curl -s -f http://${DEPLOY_IP}:${APP_PORT}/health; do sleep 2; done" || {
                        echo "Deployed container failed health check. Container output:"
                        docker logs ${APP_CONTAINER}
                        exit 1
                    }

                    echo "Deployed. App is live at http://localhost:${APP_PORT}"
                '''
            }
        }
    }

    post {
        always {
            // Remove only the test container; the deployed app keeps running
            sh 'docker rm -f ${TEST_CONTAINER} 2>/dev/null || true'
            // Clean up old dangling images to save disk space
            sh 'docker image prune -f 2>/dev/null || true'
        }
        success {
            echo "Pipeline succeeded. App deployed at http://localhost:8000"
        }
        failure {
            echo 'Pipeline failed. Check the stage logs above.'
        }
    }
}