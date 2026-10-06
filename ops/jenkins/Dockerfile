# Jenkins prêt à l'emploi : plugins, configuration et job créés au démarrage (Configuration as Code)
FROM jenkins/jenkins:lts-jdk21

USER root
ARG DOCKER_VERSION=29.8.2
ARG KUBECTL_VERSION=v1.37.1
ARG K3D_VERSION=v5.9.0
# Outils utilisés par le pipeline : client Docker, kubectl, k3d
RUN curl -fsSL "https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKER_VERSION}.tgz" \
      | tar -xz --strip-components=1 -C /usr/local/bin docker/docker \
 && curl -fsSL -o /usr/local/bin/kubectl "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" \
 && curl -fsSL -o /usr/local/bin/k3d "https://github.com/k3d-io/k3d/releases/download/${K3D_VERSION}/k3d-linux-amd64" \
 && chmod +x /usr/local/bin/kubectl /usr/local/bin/k3d
USER jenkins

ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"
ENV CASC_JENKINS_CONFIG=/usr/share/jenkins/ref/casc.yaml
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
COPY casc.yaml /usr/share/jenkins/ref/casc.yaml
