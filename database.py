"""Acesso ao banco SQLite (o arquivo banco.db é criado automaticamente)."""
import os
import sqlite3

CAMINHO_BANCO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "banco.db")


def _conectar():
    return sqlite3.connect(CAMINHO_BANCO)


def criar_tabela():
    with _conectar() as con:
        con.execute(
            """CREATE TABLE IF NOT EXISTS compromissos (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   titulo TEXT NOT NULL,
                   descricao TEXT,
                   data TEXT NOT NULL,
                   horario TEXT NOT NULL
               )"""
        )


def inserir_compromisso(titulo, descricao, data, horario):
    with _conectar() as con:
        con.execute(
            "INSERT INTO compromissos (titulo, descricao, data, horario) "
            "VALUES (?, ?, ?, ?)",
            (titulo, descricao, data, horario),
        )


def listar_compromissos():
    with _conectar() as con:
        return con.execute(
            "SELECT id, titulo, descricao, data, horario "
            "FROM compromissos ORDER BY data, horario"
        ).fetchall()


def atualizar_compromisso(id_, titulo, descricao, data, horario):
    with _conectar() as con:
        con.execute(
            "UPDATE compromissos SET titulo=?, descricao=?, data=?, horario=? "
            "WHERE id=?",
            (titulo, descricao, data, horario, id_),
        )


def excluir_compromisso(id_):
    with _conectar() as con:
        con.execute("DELETE FROM compromissos WHERE id=?", (id_,))
