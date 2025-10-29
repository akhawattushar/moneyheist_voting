from flask import Flask, render_template, request, redirect, session
import sqlite3, os

app = Flask(__name__)
app.secret_key = 'moneyheist_secret_key'

# Database setup
def init_db():
    if not os.path.exists('database.db'):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, voted INTEGER DEFAULT 0)')
        c.execute('CREATE TABLE votes (id INTEGER PRIMARY KEY, member TEXT, count INTEGER DEFAULT 0)')
        for i in range(1, 21):
            username = f"user{i}"
            c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, username))
            c.execute('INSERT INTO votes (member, count) VALUES (?, ?)', (f"Member {i}", 0))
            c.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('trial', 'trial123'))
        conn.commit()
        conn.close()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            if user[3] == 1:
                return render_template('login.html', error='You have already voted!')
            session['user'] = username
            return redirect('/vote')
        else:
            return render_template('login.html', error='Invalid credentials!')
    return render_template('login.html')

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    if 'user' not in session:
        return redirect('/')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT member FROM votes')
    members = [row[0] for row in c.fetchall()]
    conn.close()
    if request.method == 'POST':
        selected = request.form.getlist('vote')
        if selected:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            for sel in selected:
                c.execute('UPDATE votes SET count = count + 1 WHERE member=?', (sel,))
            c.execute('UPDATE users SET voted=1 WHERE username=?', (session['user'],))
            conn.commit()
            conn.close()
            session.pop('user', None)
            return render_template('thanks.html')
    return render_template('vote.html', members=members)

@app.route('/results')
def results():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT member, count FROM votes ORDER BY count DESC')
    results = c.fetchall()
    conn.close()
    return render_template('results.html', results=results)

if __name__ == '__main__':
    init_db()
    app.run(debug=False, port=5000)
