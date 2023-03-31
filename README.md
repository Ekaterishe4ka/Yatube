# Описание

Yatube - социальная сеть для публикации личных записей в тематических сообществах, с возможностью регистрации, создания собственной страницы с постами, комментариев к записям и подписками на интересующих авторов.

# Системные требования
- Python 3.7+
- Works on Linux, Windows, macOS

# Стек технологий
- Python 3.7
- Django 2.2.16

# Установка

Клонировать репозиторий и перейти в него в командной строке:

```
https://github.com/Ekaterishe4ka/Yatube.git
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
### Автор
Екатерина Богомолова
