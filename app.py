import os, time
from flask import Flask, render_template, request, send_from_directory, jsonify
from flask_socketio import SocketIO, emit, join_room
from werkzeug.utils import secure_filename
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sepilm_v14'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
socketio = SocketIO(app, cors_allowed_origins="*")

def get_db():
    db = sqlite3.connect('database.db', timeout=30)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        nickname TEXT NOT NULL,
        password TEXT NOT NULL,
        avatar TEXT,
        last_seen INTEGER DEFAULT 0
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT NOT NULL,
        receiver TEXT NOT NULL,
        msg TEXT NOT NULL,
        type TEXT DEFAULT 'text',
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    db.commit()

init_db()

@app.route('/')
def index(): return render_template('index.html')

@app.route('/back.jpg')
def background(): return send_from_directory('.', 'back.jpg')
@app.route('/mesage.mp3')
def in_sound(): return send_from_directory('.', 'mesage.mp3')
@app.route('/send.mp3')
def out_sound(): return send_from_directory('.', 'send.mp3')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files: return jsonify({"error": "No file"})
    file = request.files['file']
    filename = secure_filename(f"{int(time.time())}_{file.filename}")
    if not os.path.exists(app.config['UPLOAD_FOLDER']): os.makedirs(app.config['UPLOAD_FOLDER'])
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return jsonify({"url": f"/static/uploads/{filename}"})

@socketio.on('auth_action')
def handle_auth(data):
    db = get_db()
    user, pwd, nick, mode = data.get('user','').lower().strip(), data.get('pass',''), data.get('nick',''), data.get('mode')
    if mode == 'reg':
        if db.execute("SELECT id FROM users WHERE username=?", (user,)).fetchone():
            emit('auth_res', {'status': 'error', 'msg': 'Логин занят'})
        else:
            db.execute("INSERT INTO users (username, nickname, password) VALUES (?, ?, ?)", (user, nick, pwd))
            db.commit()
            emit('auth_res', {'status': 'ok', 'mode': 'reg'})
    else:
        u = db.execute("SELECT * FROM users WHERE username=?", (user,)).fetchone()
        if u and u['password'] == pwd:
            emit('auth_res', {'status': 'ok', 'user': user, 'nick': u['nickname'], 'avatar': u['avatar'], 'mode': 'login', 'raw_pass': pwd})
        else: emit('auth_res', {'status': 'error', 'msg': 'Ошибка входа'})

@socketio.on('load_sidebar')
def load_sidebar(me):
    db = get_db()
    rows = db.execute("SELECT DISTINCT contact FROM (SELECT receiver AS contact FROM messages WHERE sender = ? UNION SELECT sender AS contact FROM messages WHERE receiver = ?) WHERE contact IS NOT NULL", (me, me)).fetchall()
    contacts = []
    for r in rows:
        u = db.execute("SELECT nickname, avatar FROM users WHERE username=?", (r['contact'],)).fetchone()
        if u: contacts.append({'contact': r['contact'], 'nickname': u['nickname'], 'avatar': u['avatar']})
    emit('sidebar_data', contacts)

@socketio.on('join_chat')
def join_chat(data):
    me, target = data['me'], data['target'].replace('@','')
    room = "".join(sorted([me, target]))
    join_room(room)
    db = get_db()
    u = db.execute("SELECT nickname, avatar FROM users WHERE username=?", (target,)).fetchone()
    rows = db.execute("SELECT sender, msg, type FROM messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) ORDER BY timestamp ASC", (me, target, target, me)).fetchall()
    emit('history', {'room': room, 'msgs': [dict(r) for r in rows], 'target': target, 'nick': u['nickname'] if u else target, 'av': u['avatar'] if u else None})

@socketio.on('send_msg')
def handle_msg(data):
    db = get_db()
    m_type = data.get('type', 'text')
    db.execute("INSERT INTO messages (sender, receiver, msg, type) VALUES (?, ?, ?, ?)", (data['me'], data['target'], data['msg'], m_type))
    db.commit()
    emit('new_msg', {'sender': data['me'], 'text': data['msg'], 'type': m_type}, room=data['room'])
    emit('refresh_sidebar', broadcast=True)

@socketio.on('update_profile')
def update_profile(data):
    db = get_db()
    u = db.execute("SELECT password FROM users WHERE username=?", (data['user'],)).fetchone()
    new_pass = data['pass'] if data['pass'] and data['pass'].strip() != "" else u['password']
    db.execute("UPDATE users SET nickname=?, password=?, avatar=? WHERE username=?", (data['nick'], new_pass, data['avatar'], data['user']))
    db.commit()
    emit('profile_res', {'status': 'ok', 'new_pass': new_pass})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)