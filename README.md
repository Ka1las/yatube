# YATUBE
## Описание проекта
Проект Yatube предназначен для написания постов авторами, с возможностью комментирования и подписками.

Записи можно сортировать по авторам.

У каждого автора может быть свой профиль.



## Используемые технологии
- django-debug-toolbar==2.2
- Django==2.2.16
- mixer==7.1.2
- Pillow==8.3.1
- pytest==6.2.4
- pytest-django==4.4.0
- pytest-pythonpath==0.7.3
- requests==2.26.0
- six==1.16.0
- sorl-thumbnail==12.7.0
- Faker==12.0.1

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:Ka1las/yatube.git
```

```
cd yatube
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

```
source env/bin/activate
```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```
