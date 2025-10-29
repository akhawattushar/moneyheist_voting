from flask import Flask, render_template, request, redirect, session
import os

app = Flask(__name__)
app.secret_key = 'moneyheist_secret_key'

# Get database URL from environment
DATABASE_URL = os.environ.get('STORAGE_URL') or os.environ.get('POSTGRES_URL')

if DATABASE_URL:
    import psycopg2
    
    def get_db():
        return psycopg2.connect(DATABASE_URL, sslmode='require')
    
    def init_db():
        try:
            conn = get_db()
            c = conn.cursor()
            
            c.execute('''CREATE TABLE IF NOT EXISTS users 
                         (id SERIAL PRIMARY KEY, username TEXT, password TEXT, voted INTEGER DEFAULT 0)''')
            c.execute('''CREATE TABLE IF NOT EXISTS votes 
                         (id SERIAL PRIMARY KEY, member TEXT, count INTEGER DEFAULT 0)''')
            
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
        except Exception as e:
            print(f"Database init error: {e}")
else:
    print("No database URL found")

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
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
        except Exception as e:
            return f"Error: {str(e)}"
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

# Initialize database on startup
init_db()

# Vercel needs this
if __name__ != '__main__':
    # Production
    pass
