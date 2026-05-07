from flask import Flask, render_template, request, redirect, session, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = 'segredo_super_secreto'

# ------------------------
# CONFIG POSTGRESQL
# ------------------------

DATABASE_URL = "postgresql://psicogestor_db_user:MvrEi9ENanTxasj2SkEld0S9yvjFpwzW@dpg-d7t94d0k1i2s73cfoueg-a.oregon-postgres.render.com/psicogestor_db"

def conectar():
    conn = psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )
    return conn

# ------------------------
# CRIAR TABELAS
# ------------------------

def criar_tabela():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        nome TEXT,
        email TEXT,
        senha TEXT,
        foto_perfil TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pacientes (
        id SERIAL PRIMARY KEY,
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
        id SERIAL PRIMARY KEY,
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
# INDEX
# ------------------------

@app.route('/')
def index():
    return render_template('index.html')

# ------------------------
# LOGIN
# ------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form.get('email')
        senha = request.form.get('senha')

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM usuarios WHERE email=%s AND senha=%s",
            (email, senha)
        )

        usuario = cursor.fetchone()

        conn.close()

        if usuario:
            session['usuario_id'] = usuario['id']
            return redirect('/dashboard')

        return "Login inválido"

    return render_template('login.html')

# ------------------------
# CADASTRO USUÁRIO
# ------------------------

@app.route('/cadastro_usuario', methods=['GET', 'POST'])
def cadastro_usuario():

    if request.method == 'POST':

        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')

        conn = conectar()
        cursor = conn.cursor()

        # VERIFICAR SE EMAIL JÁ EXISTE
        cursor.execute(
            "SELECT * FROM usuarios WHERE email=%s",
            (email,)
        )

        usuario_existente = cursor.fetchone()

        if usuario_existente:
            conn.close()
            return "Este e-mail já está cadastrado"

        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)",
            (nome, email, senha)
        )

        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template('cadastro_usuario.html')

# ------------------------
# DASHBOARD
# ------------------------

@app.route('/dashboard')
def dashboard():

    if 'usuario_id' not in session:
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT nome FROM usuarios WHERE id=%s",
        (session['usuario_id'],)
    )

    usuario = cursor.fetchone()

    cursor.execute(
        "SELECT COUNT(*) as total FROM pacientes WHERE usuario_id=%s",
        (session['usuario_id'],)
    )

    total = cursor.fetchone()['total']

    cursor.execute('''
        SELECT a.data, a.hora, p.nome as paciente_nome
        FROM atendimentos a
        JOIN pacientes p ON a.paciente_id = p.id
        WHERE a.usuario_id=%s
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

    cursor.execute(
        "SELECT * FROM pacientes WHERE usuario_id=%s",
        (session['usuario_id'],)
    )

    lista = cursor.fetchall()

    conn.close()

    return render_template('pacientes.html', pacientes=lista)

# ------------------------
# CADASTRAR PACIENTE
# ------------------------

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
            INSERT INTO pacientes
            (nome, data_nascimento, telefone, email, observacoes, usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (
            nome,
            data,
            telefone,
            email,
            obs,
            session['usuario_id']
        ))

        conn.commit()
        conn.close()

        return redirect('/pacientes')

    return render_template('cadastro.html')

# ------------------------
# EDITAR PACIENTE
# ------------------------

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):

    if 'usuario_id' not in session:
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()

    # SALVAR ALTERAÇÕES
    if request.method == 'POST':

        nome = request.form.get('nome')
        data = request.form.get('data_nascimento')
        telefone = request.form.get('telefone')
        email = request.form.get('email')
        observacoes = request.form.get('observacoes')

        cursor.execute('''
            UPDATE pacientes
            SET nome=%s,
                data_nascimento=%s,
                telefone=%s,
                email=%s,
                observacoes=%s
            WHERE id=%s AND usuario_id=%s
        ''', (
            nome,
            data,
            telefone,
            email,
            observacoes,
            id,
            session['usuario_id']
        ))

        conn.commit()
        conn.close()

        return redirect('/pacientes')

    # CARREGAR PACIENTE
    cursor.execute(
        "SELECT * FROM pacientes WHERE id=%s AND usuario_id=%s",
        (id, session['usuario_id'])
    )

    paciente = cursor.fetchone()

    conn.close()

    return render_template('editar.html', paciente=paciente)

# ------------------------
# EXCLUIR PACIENTE
# ------------------------

@app.route('/excluir/<int:id>')
def excluir(id):

    if 'usuario_id' not in session:
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM pacientes WHERE id=%s AND usuario_id=%s",
        (id, session['usuario_id'])
    )

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

    # CADASTRAR ATENDIMENTO
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
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (
            paciente,
            data,
            hora,
            obs,
            tipo,
            link,
            session['usuario_id']
        ))

        conn.commit()
        conn.close()

        return redirect('/agenda')

    # LISTAR PACIENTES
    cursor.execute(
        "SELECT id, nome FROM pacientes WHERE usuario_id=%s",
        (session['usuario_id'],)
    )

    pacientes = cursor.fetchall()

    # LISTAR ATENDIMENTOS
    cursor.execute('''
        SELECT a.id, p.nome, a.data, a.hora, a.tipo, a.link
        FROM atendimentos a
        JOIN pacientes p ON a.paciente_id = p.id
        WHERE a.usuario_id=%s
        ORDER BY a.data ASC, a.hora ASC
    ''', (session['usuario_id'],))

    atendimentos = cursor.fetchall()

    conn.close()

    return render_template(
        'agenda.html',
        pacientes=pacientes,
        atendimentos=atendimentos
    )

# ------------------------
# EXCLUIR ATENDIMENTO
# ------------------------

@app.route('/excluir_atendimento/<int:id>')
def excluir_atendimento(id):

    if 'usuario_id' not in session:
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM atendimentos WHERE id=%s AND usuario_id=%s",
        (id, session['usuario_id'])
    )

    conn.commit()
    conn.close()

    return redirect('/agenda')

# ------------------------
# API PACIENTES
# ------------------------

@app.route('/api/pacientes')
def api_pacientes():

    if 'usuario_id' not in session:
        return jsonify({"erro": "não autorizado"}), 401

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, nome, telefone, email FROM pacientes WHERE usuario_id=%s",
        (session['usuario_id'],)
    )

    pacientes = cursor.fetchall()

    conn.close()

    return jsonify(pacientes)

# ------------------------
# API ATENDIMENTOS
# ------------------------

@app.route('/api/atendimentos')
def api_atendimentos():

    if 'usuario_id' not in session:
        return jsonify({"erro": "não autorizado"}), 401

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT a.id, p.nome as paciente, a.data, a.hora, a.tipo
        FROM atendimentos a
        JOIN pacientes p ON a.paciente_id = p.id
        WHERE a.usuario_id=%s
    ''', (session['usuario_id'],))

    atendimentos = cursor.fetchall()

    conn.close()

    return jsonify(atendimentos)

# ------------------------
# LOGOUT
# ------------------------

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')

# ------------------------
# RUN
# ------------------------

if __name__ == '__main__':
    app.run()
    