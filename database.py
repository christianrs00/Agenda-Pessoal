import sqlite3
from rich import inspect
from rich import print

def ligar_db():
    """ Estabelece a ligação com o Banco de dados """
    return sqlite3.connect("agenda.db")

def criar_tabela():

    """ Cria a tabela de compromissos se ainda não existir """

    conn = ligar_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compromissos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descricao TEXT,
            data TEXT NOT NULL,
            horario TEXT NOT NULL,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.commit()
    conn.close()

def inserir_compromisso(titulo, descricao, data, horario):

    """ Insere um novo compromisso na base de dados """

    conn = ligar_db()
    cursor = conn.cursor()
    cursor.execute(
        """
            INSERT INTO compromissos (titulo, descricao, data, horario)
            VALUES (?, ?, ?, ?)
        """,
(titulo, descricao, data, horario),
    )
    conn.commit()
    conn.close()

def listar_compromissos():

    """ Retorna todos os compromissos ordenados por data e horários """

    conn = ligar_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, titulo, descricao, data, horario FROM compromissos ORDER BY "
        " data, horario"
    )
    resultados = cursor.fetchall()
    conn.close()
    return resultados

def excluir_compromisso(id_comp):

    """ Elimina um compromisso com base no ID """

    conn = ligar_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM compromissos WHERE id = ?", (id_comp,))
    conn.commit()
    conn.close()

def consultar_por_data(data):

    """ Filtra os compromissos de uma data específica """

    conn = ligar_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, titulo, descricao, data, horario FROM compromissos WHERE data = ? ORDER BY horario
    """, (data,),
    )
    resultados = cursor.fetchall()
    conn.close()
    return resultados
