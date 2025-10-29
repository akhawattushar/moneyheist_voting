from flask import Flask, render_template, request, redirect, session
import os
import psycopg2

app = Flask(__name__)
app.secret_key = 'moneyheist_secret_key'

# Database URL from Vercel
DATABASE_URL = os.environ.get('STORAGE_URL')  # Changed from POSTGRES_URL

def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    # Create tables if they don't exist
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id SERIAL PRIMARY KEY, username TEXT, password TEXT, voted INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS votes 
                 (id SERIAL PRIMARY KEY, member TEXT, count INTEGER DEFAULT 0)''')
    
    # Check if data already exists
    c.execute('SELECT COUNT(*) FROM users')
    if c.fetchone()[0] == 0:
        names = ["John", "Sarah", "Mike", "Emma", "David", "Lisa", "Tom", "Anna", 
                 "Chris", "Maria", "Alex", "Nina", "Ryan", "Sophie", "Jake", 
                 "Olivia", "Liam", "Zoe", "Max", "Emily"]
        
        for i in range(1, 21):
            username = f"user{i}"
            c.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, username))
            c.execute('INSERT INTO votes (member, count) VALUES (%s, %s)', (names[i-1], 0))
        
        c.execute('INSERT INTO users (username, password) VALUES (%s, %s)', ('trial', 'trial123'))
    
    conn.commit()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username=%s AND password=%s', (username, password))
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
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT member FROM votes')
    members = [row[0] for row in c.fetchall()]
    conn.close()
    if request.method == 'POST':
        selected = request.form.getlist('vote')
        if selected:
            conn = get_db()
            c = conn.cursor()
            for sel in selected:
                c.execute('UPDATE votes SET count = count + 1 WHERE member=%s', (sel,))
            c.execute('UPDATE users SET voted=1 WHERE username=%s', (session['user'],))
            conn.commit()
            conn.close()
            session.pop('user', None)
            return render_template('thanks.html')
    return render_template('vote.html', members=members)

@app.route('/results')
def results():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT member, count FROM votes ORDER BY count DESC')
    results = c.fetchall()
    conn.close()
    return render_template('results.html', results=results)

if __name__ == '__main__':
    init_db()
    app.run(debug=False, port=5000)

