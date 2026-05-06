from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3

app = Flask(__name__)
app.secret_key = 'segredo_super_secreto'

# ------------------------
# BANCO
# ------------------------
def conectar():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabela():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT,
        senha TEXT,
        foto_perfil TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pacientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        data_nascimento TEXT,
        telefone TEXT,
        email TEXT,
        observacoes TEXT,
        usuario_id INTEGER
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS atendimentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER,
        data TEXT,
        hora TEXT,
        observacoes TEXT,
        tipo TEXT,
        link TEXT,
        usuario_id INTEGER
    )
    ''')

    conn.commit()
    conn.close()

criar_tabela()

# ------------------------
# LOGIN / DASHBOARD
# ------------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM usuarios WHERE email=? AND senha=?", (email, senha))
        usuario = cursor.fetchone()
        conn.close()

        if usuario:
            session['usuario_id'] = usuario['id']
            return redirect('/dashboard')

        return "Login inválido"

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT nome FROM usuarios WHERE id=?", (session['usuario_id'],))
    usuario = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) as total FROM pacientes WHERE usuario_id=?", (session['usuario_id'],))
    total = cursor.fetchone()['total']

    cursor.execute('''
        SELECT a.data, a.hora, p.nome as paciente_nome
        FROM atendimentos a
        JOIN pacientes p ON a.paciente_id = p.id
        WHERE a.usuario_id=?
        ORDER BY a.data ASC, a.hora ASC
        LIMIT 5
    ''', (session['usuario_id'],))

    atendimentos = cursor.fetchall()

    conn.close()

    return render_template(
        'dashboard.html',
        usuario=usuario,
        total_pacientes=total,
        atendimentos=atendimentos
    )

# ------------------------
# PACIENTES
# ------------------------

@app.route('/pacientes')
def pacientes():
    if 'usuario_id' not in session:
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM pacientes WHERE usuario_id=?", (session['usuario_id'],))
    lista = cursor.fetchall()

    conn.close()

    return render_template('pacientes.html', pacientes=lista)


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if 'usuario_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        nome = request.form.get('nome')
        data = request.form.get('data_nascimento')
        telefone = request.form.get('telefone')
        email = request.form.get('email')
        obs = request.form.get('observacoes')

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO pacientes (nome, data_nascimento, telefone, email, observacoes, usuario_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (nome, data, telefone, email, obs, session['usuario_id']))

        conn.commit()
        conn.close()

        return redirect('/pacientes')

    return render_template('cadastro.html')


@app.route('/excluir/<int:id>')
def excluir(id):
    if 'usuario_id' not in session:
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM pacientes WHERE id=? AND usuario_id=?", (id, session['usuario_id']))

    conn.commit()
    conn.close()

    return redirect('/pacientes')

# ------------------------
# AGENDA
# ------------------------

@app.route('/agenda', methods=['GET', 'POST'])
def agenda():
    if 'usuario_id' not in session:
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()

    if request.method == 'POST':
        paciente = request.form.get('paciente')
        data = request.form.get('data')
        hora = request.form.get('hora')
        obs = request.form.get('observacoes')
        tipo = request.form.get('tipo')
        link = request.form.get('link')

        cursor.execute('''
            INSERT INTO atendimentos 
            (paciente_id, data, hora, observacoes, tipo, link, usuario_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (paciente, data, hora, obs, tipo, link, session['usuario_id']))

        conn.commit()
        conn.close()

        return redirect('/agenda')

    cursor.execute("SELECT id, nome FROM pacientes WHERE usuario_id=?", (session['usuario_id'],))
    pacientes = cursor.fetchall()

    cursor.execute('''
        SELECT a.id, p.nome, a.data, a.hora, a.tipo, a.link
        FROM atendimentos a
        JOIN pacientes p ON a.paciente_id = p.id
        WHERE a.usuario_id=?
        ORDER BY a.data ASC, a.hora ASC
    ''', (session['usuario_id'],))

    atendimentos = cursor.fetchall()

    conn.close()

    return render_template('agenda.html', pacientes=pacientes, atendimentos=atendimentos)


@app.route('/excluir_atendimento/<int:id>')
def excluir_atendimento(id):
    if 'usuario_id' not in session:
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM atendimentos WHERE id=? AND usuario_id=?",
        (id, session['usuario_id'])
    )

    conn.commit()
    conn.close()

    return redirect('/agenda')

# ------------------------
# 🔥 API (REQUISITO DO PROJETO)
# ------------------------

@app.route('/api/pacientes')
def api_pacientes():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT id, nome, telefone, email FROM pacientes")
    pacientes = cursor.fetchall()

    lista = [dict(p) for p in pacientes]

    conn.close()
    return jsonify(lista)


@app.route('/api/atendimentos')
def api_atendimentos():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT a.id, p.nome as paciente, a.data, a.hora, a.tipo
        FROM atendimentos a
        JOIN pacientes p ON a.paciente_id = p.id
    ''')

    atendimentos = cursor.fetchall()

    lista = [dict(a) for a in atendimentos]

    conn.close()
    return jsonify(lista)

# ------------------------
# LOGOUT
# ------------------------

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)