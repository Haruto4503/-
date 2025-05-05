from flask import Flask, request, redirect, url_for, flash, get_flashed_messages, render_template_string
import os
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Создаем папку для изображений
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# Инициализация базы данных
def init_db():
    with sqlite3.connect('museum.db') as conn:
        c = conn.cursor()
        # Таблица пользователей
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        # Таблица экспонатов
        c.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                image TEXT NOT NULL
            )
        ''')
        conn.commit()


init_db()


# Вспомогательные функции для работы с базой
def get_db_connection():
    conn = sqlite3.connect('museum.db')
    conn.row_factory = sqlite3.Row
    return conn


# Главная страница
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if 'register' in request.form:
            username = request.form['username']
            password = request.form['password']
            try:
                with get_db_connection() as conn:
                    conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
                flash('Регистрация успешна!')
            except sqlite3.IntegrityError:
                flash('Пользователь с таким именем уже существует!')
        elif 'login' in request.form:
            username = request.form['username']
            password = request.form['password']
            with get_db_connection() as conn:
                user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?',
                                    (username, password)).fetchone()
                if user:
                    flash('Вы успешно вошли!')
                    return redirect(url_for('museum'))
                else:
                    flash('Неверные учетные данные!')
    flash_messages = get_flashed_messages()
    return render_template_string('''

<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Регистрация и Вход</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f0f8ff;
        }
        h1 {
            color: #4CAF50;
            text-align: center;
        }
        .container {
            max-width: 400px;
            margin: auto;
            padding: 20px;
            border: 1px solid #ccc;
            border-radius: 10px;
            background-color: white;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        .form-group button {
            width: 100%;
            padding: 10px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .form-group button:hover {
            background-color: #45a049;
        }
        p {
            text-align: center;
        }
        .flash {
            color: red;
            text-align: center;
        }
    </style>
</head>
<body>
    <h1>Регистрация и Вход</h1>
    <div class="container" id="auth">
        <div class="flash">
            {% if flash_messages %}
                {{ flash_messages | join("<br>") | safe }}
            {% endif %}
        </div>

        <h2>Вход</h2>
        <form method="POST">
            <div class="form-group">
                <input type="text" name="username" placeholder="Имя пользователя" required/>
            </div>
            <div class="form-group">
                <input type="password" name="password" placeholder="Пароль" required/>
            </div>
            <div class="form-group">
                <button type="submit" name="login">Войти</button>
            </div>
            <p>Нет аккаунта? <span id="showRegister">Зарегистрироваться</span></p>
        </form>

        <div id="registerForm" class="hidden">
            <h2>Регистрация</h2>
            <form method="POST">
                <div class="form-group">
                    <input type="text" name="username" placeholder="Имя пользователя" required/>
                </div>
                <div class="form-group">
                    <input type="password" name="password" placeholder="Пароль" required/>
                </div>
                <div class="form-group">
                    <button type="submit" name="register">Зарегистрироваться</button>
                </div>
                <p>Уже есть аккаунт? <span id="showLogin">Войти</span></p>
            </form>
        </div>
    </div>

    <script src="{{ url_for('static', filename='app.js') }}"></script>
</body>
</html>

    ''', flash_messages=flash_messages)


# Страница музея
@app.route('/museum', methods=['GET', 'POST'])
def museum():
    if request.method == 'POST':
        if 'add_item' in request.form:
            title = request.form['item_title']
            description = request.form['item_description']
            if 'image' in request.files:
                image = request.files['image']
                if image.filename:
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
                    image.save(image_path)
                    with get_db_connection() as conn:
                        conn.execute(
                            'INSERT INTO items (title, description, image) VALUES (?, ?, ?)',
                            (title, description, image.filename)
                        )
                    flash('Экспонат добавлен!')
        elif 'delete_item' in request.form:
            item_id = int(request.form['item_id'])
            with get_db_connection() as conn:
                item = conn.execute('SELECT * FROM items WHERE id = ?', (item_id,)).fetchone()
                if item:
                    # Удаляем изображение
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], item['image'])
                    if os.path.exists(image_path):
                        os.remove(image_path)
                    conn.execute('DELETE FROM items WHERE id = ?', (item_id,))
                    flash('Экспонат удалён!')
        elif 'edit_item' in request.form:
            item_id = int(request.form['item_id'])
            return redirect(url_for('edit_item', item_id=item_id))
    flash_messages = get_flashed_messages()
    with get_db_connection() as conn:
        items = conn.execute('SELECT * FROM items').fetchall()
    return render_template_string('''
   <!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Личный музей</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f0f8ff;
        }
        h1 {
            color: #4CAF50;
            text-align: center;
        }
        p {
            font-size: 30px;
            line-height: 1.5;
        }
        .flash {
            color: red;
            text-align: center;
        }
        .item {
            margin: 30px 0;
            padding: 30px;
            border: 1px solid #ccc;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        img {
            max-width: 80%; /* Заставляет изображение заполнять ширину контейнера */
            height: auto; /* Сохраняет пропорции изображения */
            border-radius: 10px;
        }
        .button-group {
            display: flex;
            justify-content: space-between;
            margin-top: 10px;
        }
        .button-group form {
            flex: 1; /* Заставляет формы занимать равное пространство */
        }
        .button-group button {
            padding: 10px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            width: 100%;
            margin: 0 5px;
        }
        .button-group button:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
    <h1>Личный музей</h1>
    <a href="{{ url_for('home') }}">На главную</a>
    {% if flash_messages %}
        <p class="flash">{{ flash_messages | join("<br>") | safe }}</p>
    {% endif %}
    <h2>Добавить экспонат</h2>
    <form method="POST" enctype="multipart/form-data">
        <input type="text" name="item_title" placeholder="Название экспоната" required/>
        <textarea name="item_description" placeholder="Описание экспоната" required></textarea>
        <input type="file" name="image" accept="image/*" required/>
        <button type="submit" name="add_item">Добавить экспонат</button>
    </form>
    <h2>Экспонаты</h2>
    <div>
        {% for item in items %}
            <div class="item">
                <h4>{{ item['title'] }}</h4>
                <img src="{{ url_for('static', filename='uploads/' + item['image']) }}" alt="{{ item['title'] }}"/>
                <p>{{ item['description'] }}</p>
                <div class="button-group">
                    <form method="POST" style="flex: 1;">
                        <input type="hidden" name="item_id" value="{{ item['id'] }}"/>
                        <button type="submit" name="edit_item">Редактировать</button>
                    </form>
                    <form method="POST" style="flex: 1;">
                        <input type="hidden" name="item_id" value="{{ item['id'] }}"/>
                        <button type="submit" name="delete_item">Удалить экспонат</button>
                    </form>
                </div>
            </div>
        {% endfor %}
    </div>
</body>
</html>

    ''', items=items, flash_messages=flash_messages)


# Страница редактирования экспоната
@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    with get_db_connection() as conn:
        item = conn.execute('SELECT * FROM items WHERE id = ?', (item_id,)).fetchone()
    if not item:
        flash('Экспонат не найден')
        return redirect(url_for('museum'))

    if request.method == 'POST':
        new_title = request.form['item_title']
        new_description = request.form['item_description']

        if 'image' in request.files:
            image = request.files['image']
            if image.filename:
                # Удаляем старое изображение
                old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], item['image'])
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
                # Сохраняем новое изображение
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
                image.save(image_path)
                # Обновляем изображение и другие данные
                with get_db_connection() as conn:
                    conn.execute('UPDATE items SET title = ?, description = ?, image = ? WHERE id = ?',
                                 (new_title, new_description, image.filename, item_id))
            else:
                # Если новое изображение не загружено, просто обновляем настройки без изменения изображения
                with get_db_connection() as conn:
                    conn.execute('UPDATE items SET title = ?, description = ? WHERE id = ?',
                                 (new_title, new_description, item_id))

        flash('Экспонат обновлен!')
        return redirect(url_for('museum'))

    # Отображение формы редактирования
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>Редактировать экспонат</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f0f8ff; }
                h1 { color: #4CAF50; }
                form { max-width: 500px; }
                label { display: block; margin-top: 10px; font-weight: bold; }
                input[type="text"], textarea { width: 100%; padding: 8px; margin-top: 5px; box-sizing: border-box; }
                button { margin-top: 15px; padding: 10px 20px; background-color: #4CAF50; color: white; border: none; cursor: pointer; }
                button:hover { background-color: #45a049; }
            </style>
        </head>
        <body>
            <h1>Редактировать экспонат</h1>
            <form method="POST" enctype="multipart/form-data">
                <label>Название:</label>
                <input type="text" name="item_title" value="{{ item['title'] }}" required/>

                <label>Описание:</label>
                <textarea name="item_description" required>{{ item['description'] }}</textarea>

                <label>Новое изображение (оставьте пустым, чтобы оставить старое):</label>
                <input type="file" name="image" accept="image/*"/>

                <button type="submit">Обновить</button>
            </form>
        </body>
        </html>
    ''', item=item)


# Запуск приложения
if __name__ == '__main__':
    app.run(debug=True)
