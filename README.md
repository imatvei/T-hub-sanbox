1. Клонируем репозиторий

git clone -b task_get_airports https://github.com/imatvei/T-hub-sanbox.git

cd T-hub-sanbox
2. Создаём файл с настройками 

Copy-Item .env.example .env

linux/macos

cp .env.example .env

3. Запуск БД

docker-compose up -d

4. Установка зависимостей в виртуальном окружении

python -m venv .venv

.venv\Scripts\activate

linux/maсos

source .venv/bin/activate

pip install -r requirements.txt

5. Запуск

python run.py