pipeline {
    agent any
    stage('Coverage') {
        steps {
            sh "mkdir -p coverage-reports/"
            // install the python packages
            sh "pipenv install --dev"
            sh "coverage run pytest"
            sh "coverage xml -i -o coverage-reports/coverage.xml"
            stash name:"coverage", includes:"coverage-reports/coverage.xml"
            
        }
    }
    stage('Sonarqube') {
        environment {
            scannerHome = tool 'sonarscanner_4.2.0.1873'
        }
        steps {
            unstash name: "coverage"
            withSonarQubeEnv('housenet') {
                sh "${scannerHome}/bin/sonar-scanner -D sonar.projectName=pygoodwe -D sonar.projectKey=pygoodwe -D sonar.sources=."
            }

        }
    }
    stage ('Build') {
        steps {
            sh "pipenv install --dev && pipenv run python setup.py sdist bdist_wheel"
        }
    }
}