import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'arcade.db')

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    """Inicializa as tabelas do banco de dados SQLite caso ainda não existam."""
    conn = get_connection()
    cursor = conn.cursor()

    # Tabela de Jogadores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jogadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabela de Partidas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS partidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jogador_id INTEGER NOT NULL,
            jogo TEXT NOT NULL,
            nivel INTEGER DEFAULT 2,
            pontuacao INTEGER DEFAULT 0,
            tempo_segundos REAL DEFAULT 0.0,
            derrotou_zecreppe INTEGER DEFAULT 0,
            venceu INTEGER DEFAULT 1,
            data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(jogador_id) REFERENCES jogadores(id)
        )
    ''')

    # Garante a existência da coluna nivel em tabelas pré-existentes
    cursor.execute("PRAGMA table_info(partidas)")
    colunas = [col[1] for col in cursor.fetchall()]
    if 'nivel' not in colunas:
        cursor.execute("ALTER TABLE partidas ADD COLUMN nivel INTEGER DEFAULT 1")

    conn.commit()
    conn.close()


def resetar_placar_space_invaders():
    """Zera o ranking persistido do Space Invaders."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM partidas WHERE jogo = 'space_invaders'")
    cursor.execute("DELETE FROM jogadores WHERE id NOT IN (SELECT DISTINCT jogador_id FROM partidas)")

    conn.commit()
    conn.close()


def obter_ou_criar_jogador(nome):
    """Busca um jogador pelo nome ou o cadastra se for novo. Retorna o ID."""
    nome = nome.strip()[:10]  # Limite máximo de 10 caracteres
    if not nome:
        return None

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM jogadores WHERE LOWER(nome) = LOWER(?)', (nome,))
    row = cursor.fetchone()

    if row:
        jogador_id = row[0]
    else:
        cursor.execute('INSERT INTO jogadores (nome) VALUES (?)', (nome,))
        conn.commit()
        jogador_id = cursor.lastrowid

    conn.close()
    return jogador_id

def salvar_partida_space_invaders(jogador_id, pontuacao, tempo_segundos=0.0, nivel=1):
    """
    Salva a pontuação do Space Invaders.
    - Se o jogador já possuir registro, atualiza se a nova pontuação for maior.
    - Mantém apenas os 20 melhores registros no ranking, excluindo os excedentes.
    """
    conn = get_connection()
    cursor = conn.cursor()
    agora_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        SELECT id, pontuacao, tempo_segundos FROM partidas
        WHERE jogador_id = ? AND jogo = 'space_invaders'
    ''', (jogador_id,))
    row = cursor.fetchone()

    if row:
        partida_id, pontuacao_antiga, tempo_antigo = row
        if pontuacao > pontuacao_antiga or (pontuacao == pontuacao_antiga and tempo_segundos > (tempo_antigo or 0.0)):
            cursor.execute('''
                UPDATE partidas
                SET pontuacao = ?, tempo_segundos = ?, nivel = ?, data_hora = ?
                WHERE id = ?
            ''', (pontuacao, tempo_segundos, nivel, agora_str, partida_id))
    else:
        cursor.execute('''
            INSERT INTO partidas (jogador_id, jogo, pontuacao, tempo_segundos, nivel, data_hora)
            VALUES (?, 'space_invaders', ?, ?, ?, ?)
        ''', (jogador_id, pontuacao, tempo_segundos, nivel, agora_str))

    conn.commit()

    # MANTER APENAS OS TOP 20
    cursor.execute('''
        DELETE FROM partidas
        WHERE jogo = 'space_invaders'
        AND id NOT IN (
            SELECT id FROM partidas
            WHERE jogo = 'space_invaders'
            ORDER BY pontuacao DESC, data_hora ASC
            LIMIT 20
        )
    ''')

    conn.commit()
    conn.close()

def salvar_partida_adventure(jogador_id, tempo_segundos, derrotou_zecreppe=0, venceu=1, nivel=2):
    """
    Salva o resultado do Adventure com nível de dificuldade.
    Se o jogador derrotou ZéCreppe, salva como Vencedor Original.
    Atualiza se obtiver tempo menor para a mesma categoria de vitória.
    """
    conn = get_connection()
    cursor = conn.cursor()
    agora_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        SELECT id, tempo_segundos, derrotou_zecreppe FROM partidas
        WHERE jogador_id = ? AND jogo = 'adventure' AND derrotou_zecreppe = ?
    ''', (jogador_id, derrotou_zecreppe))
    row = cursor.fetchone()

    if row:
        partida_id, tempo_antigo, _ = row
        if tempo_segundos < tempo_antigo or tempo_antigo == 0:
            cursor.execute('''
                UPDATE partidas
                SET tempo_segundos = ?, venceu = ?, nivel = ?, data_hora = ?
                WHERE id = ?
            ''', (tempo_segundos, venceu, nivel, agora_str, partida_id))
    else:
        cursor.execute('''
            INSERT INTO partidas (jogador_id, jogo, pontuacao, tempo_segundos, derrotou_zecreppe, venceu, nivel, data_hora)
            VALUES (?, 'adventure', 0, ?, ?, ?, ?, ?)
        ''', (jogador_id, tempo_segundos, derrotou_zecreppe, venceu, nivel, agora_str))

    conn.commit()
    conn.close()

def obter_ranking_space_invaders(limit=20):
    """Retorna o Top 20 do Space Invaders com pontuação e tempo sobrevivido."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT j.nome, p.pontuacao, p.tempo_segundos, p.data_hora
        FROM partidas p
        JOIN jogadores j ON p.jogador_id = j.id
        WHERE p.jogo = 'space_invaders'
        ORDER BY p.pontuacao DESC, p.tempo_segundos DESC, p.data_hora ASC
        LIMIT ?
    ''', (limit,))

    rows = cursor.fetchall()
    conn.close()

    resultado = []
    for idx, (nome, pts, tempo_seg, dt) in enumerate(rows, 1):
        tempo_seg = float(tempo_seg or 0.0)
        resultado.append({
            'posicao': idx,
            'nome': nome,
            'pontuacao': pts,
            'tempo_segundos': tempo_seg,
            'tempo': formatar_tempo(tempo_seg) if tempo_seg > 0 else 'N/A',
            'data': dt
        })
    return resultado

def formatar_tempo(segundos):
    mins = int(segundos) // 60
    secs = int(segundos) % 60
    return f"{mins:02d}:{secs:02d}"

def obter_vencedores_originais_adventure(limit=20):
    """Retorna os Vencedores Originais (derrotaram ZéCreppe): (pos, nome, tempo_str, data)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT j.nome, p.tempo_segundos, p.data_hora
        FROM partidas p
        JOIN jogadores j ON p.jogador_id = j.id
        WHERE p.jogo = 'adventure' AND p.derrotou_zecreppe = 1
        ORDER BY p.tempo_segundos ASC, p.data_hora ASC
        LIMIT ?
    ''', (limit,))

    rows = cursor.fetchall()
    conn.close()

    resultado = []
    for idx, (nome, tempo_sec, dt) in enumerate(rows, 1):
        resultado.append({
            'posicao': idx,
            'nome': nome,
            'tempo': formatar_tempo(tempo_sec),
            'data': dt
        })
    return resultado

def obter_vencedores_normais_adventure(limit=20):
    """Retorna os vencedores normais do Adventure: (pos, nome, tempo_str, data)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT j.nome, p.tempo_segundos, p.data_hora
        FROM partidas p
        JOIN jogadores j ON p.jogador_id = j.id
        WHERE p.jogo = 'adventure' AND p.venceu = 1 AND p.derrotou_zecreppe = 0
        ORDER BY p.tempo_segundos ASC, p.data_hora ASC
        LIMIT ?
    ''', (limit,))

    rows = cursor.fetchall()
    conn.close()

    resultado = []
    for idx, (nome, tempo_sec, dt) in enumerate(rows, 1):
        resultado.append({
            'posicao': idx,
            'nome': nome,
            'tempo': formatar_tempo(tempo_sec),
            'data': dt
        })
    return resultado
