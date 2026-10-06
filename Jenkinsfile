// Pipeline CI/CD de SECOMO : build, scan de sécurité, déploiement sur Kubernetes (k3d)
// et tests d'intégration contre l'application déployée.
pipeline {
  agent any

  options {
    timestamps()
    timeout(time: 30, unit: 'MINUTES')
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '15'))
  }

  environment {
    TAG = "${env.BUILD_NUMBER}-${env.GIT_COMMIT.take(7)}"
    APP_URL = 'http://localhost:8081'
  }

  stages {
    stage('Build des images') {
      steps {
        sh 'docker build -t secomo-backend:$TAG backend'
        sh '''docker build -t secomo-frontend:$TAG \
              --build-arg VITE_API_BASE=$APP_URL \
              --build-arg VITE_WS_BASE=ws://localhost:8081 frontend'''
      }
    }

    stage('Scan de sécurité (Trivy)') {
      steps {
        sh '''
          mkdir -p reports
          for img in backend frontend; do
            docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v trivy-cache:/root/.cache \
              aquasec/trivy:0.75.0 image --quiet --scanners vuln --severity HIGH,CRITICAL \
              --format table secomo-$img:$TAG > reports/trivy-$img.txt
          done
        '''
        // Mode rapport : les vulnérabilités sont archivées avec le build, sans bloquer le déploiement
        sh 'tail -n 5 reports/trivy-*.txt || true'
      }
    }

    stage('Déploiement sur Kubernetes') {
      steps {
        sh 'ops/deploy.sh $TAG'
      }
    }

    stage('Tests contre le cluster') {
      steps {
        sh '''
          cid=$(docker create --network host -e API_URL=$APP_URL python:3.12-slim \
                sh -c "cd /tmp && pip install -q --root-user-action=ignore -r requirements-dev.txt && pytest tests -v --junitxml=report.xml")
          docker cp backend/tests "$cid:/tmp/tests"
          docker cp backend/requirements-dev.txt "$cid:/tmp/requirements-dev.txt"
          status=0
          docker start -a "$cid" || status=$?
          docker cp "$cid:/tmp/report.xml" reports/tests.xml || true
          docker rm "$cid" > /dev/null
          exit $status
        '''
      }
    }
  }

  post {
    always {
      junit allowEmptyResults: true, testResults: 'reports/tests.xml'
      archiveArtifacts artifacts: 'reports/*', allowEmptyArchive: true
    }
    success {
      echo "SECOMO ${env.TAG} est en ligne : ${env.APP_URL} · Grafana : ${env.APP_URL}/grafana"
    }
  }
}
