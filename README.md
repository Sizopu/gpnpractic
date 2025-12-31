Само задание выполнено не полность, ибо я хотел сделать задание с двумя разными виртуальными машинами, но из-за нехватки ресурсов у меня падал миникуб. На само задание я убил достаточно много времени, выполнил не идеально, но что есть.
(Прошу прощения за позднюю отправку, не думал что это займет много времени) (helm templates, compose ci/local)


curl -LO https://github.com/kubernetes/minikube/releases/latest/download/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube && rm minikube-linux-amd64
 
 Установка minikube

sudo apt update
sudo apt install -y docker.io

 ![alt text](photo/image.png)
 
 ![alt text](photo/image1.png)
 
 ![alt text](image.png)
 ![alt text](image-1.png)

 Установка Gitlab

 ![alt text](image-2.png)
 ![alt text](image-3.png)
 ![alt text](image-4.png)
 ![alt text](image-5.png)

 Логин на GitLab

 ![alt text](image-6.png)

sudo cat /etc/gitlab/initial_root_password
R9!tQe7M@42p root
 
 ![alt text](image-7.png)
SSH:
 
 ![alt text](image-8.png)
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh root@192.168.0.116 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"

https://docs.docker.com/engine/install/ubuntu/
 
 Установка docker для раннера Gitlab
 ![alt text](image-9.png)
 
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
 

 

Gitlab runner
 
 ![alt text](image-11.png)
 ![alt text](image-10.png)
 ![alt text](image-12.png)
 ![alt text](image-13.png)
 ![alt text](image-14.png)
![alt text](image-15.png)
 ![alt text](image-16.png)

Настройка ssh между minikube и gitlab

![alt text](image-17.png)
![alt text](image-18.png)
![alt text](image-19.png)
![alt text](image-20.png)

Запустим тестовый пайплайн (находится в k8s):
test:
  image: alpine:latest
  tags:
    - docker-runner
  script:
    - echo "Runner works!"
    - uname -a


 
Minikube-status

Deploy:
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  namespace: demo
spec:
  replicas: 1
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: nginx
          image: nginx:alpine
          ports:
            - containerPort: 80

Namespace:
apiVersion: v1
kind: Namespace
metadata:
  name: demo

svc:
apiVersion: v1
kind: Service
metadata:
  name: web
  namespace: demo
spec:
  type: NodePort
  selector:
    app: web
  ports:
    - port: 80
      targetPort: 80
      nodePort: 30080

 gitlav-ci.yml:
stages:
  - deploy

deploy_minikube:
  stage: deploy
  image: alpine:latest
  tags:
    - docker-runner

  before_script:
    - apk add --no-cache openssh-client bash
    - mkdir -p ~/.ssh
    - echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_ed25519
    - chmod 600 ~/.ssh/id_ed25519
    - ssh-keyscan -H "$MINIKUBE_HOST" >> ~/.ssh/known_hosts

  script:
    - |
      ssh -i ~/.ssh/id_ed25519 "$MINIKUBE_USER@$MINIKUBE_HOST" 'bash -lc "
        set -e

        echo \"== Cluster ==\"
        kubectl get nodes -o wide

        echo \"== Copy manifests ==\"
        rm -rf /tmp/k8s
        mkdir -p /tmp/k8s
      "'

    - scp -i ~/.ssh/id_ed25519 -r k8s/* "$MINIKUBE_USER@$MINIKUBE_HOST:/tmp/k8s/"

    - |
      ssh -i ~/.ssh/id_ed25519 "$MINIKUBE_USER@$MINIKUBE_HOST" 'bash -lc "
        set -e

        echo \"== Ensure namespace ==\"
        kubectl get ns demo >/dev/null 2>&1 || kubectl create ns demo

        echo \"== Clean old resources ==\"
        kubectl -n demo delete deploy web --ignore-not-found
        kubectl -n demo delete svc web --ignore-not-found
        kubectl -n demo delete pods -l app=web --ignore-not-found

        echo \"== Apply new manifests ==\"
        kubectl apply -f /tmp/k8s

        echo \"== Wait for rollout ==\"
        kubectl -n demo rollout status deploy/web --timeout=180s
        kubectl -n demo wait --for=condition=Ready pod -l app=web --timeout=180s

        echo \"== Result ==\"
        kubectl -n demo get deploy,svc,pods -o wide

        echo \"== Open ==\"
        echo http://192.168.49.2:30080
      "'




Kubectl на minikube
На Minikube VM (192.168.0.117):
Скачать kubectl
curl -LO https://dl.k8s.io/release/v1.34.3/bin/linux/amd64/kubectl
Проверка:
ls -lh kubectl

Сделать исполняемым и установить
chmod +x kubectl

Проверка
kubectl version --client
kubectl get nodes -o wide
Ожидаемо:
Client Version: v1.34.3
minikube   Ready   control-plane   v1.34.0

 ![alt text](image-21.png)
 ![alt text](image-22.png)
 ![alt text](image-23.png)


Docker-compose:
Отработка по всем контейнерам
 
 ![alt text](image-24.png)
 
![alt text](image-25.png)
 ![alt text](image-26.png)
 ![alt text](image-27.png)
 ![alt text](image-28.png)
 ![alt text](image-29.png)
 ![alt text](image-30.png)

Теперь настройка манифестов и пропись helm чартов.
 ![alt text](image-31.png)
 ![alt text](image-32.png)
 ![alt text](image-33.png)
 ![alt text](image-34.png)

 (Тут проблема с ресурсами и т.д......)
curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
 
