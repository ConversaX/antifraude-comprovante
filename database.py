import sqlite3
from datetime import datetime

DB_PATH = "fraudes.db"


def criar_tabelas():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analises (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                hash_imagem  TEXT UNIQUE NOT NULL,
                endereco     TEXT,
                score_risco  INTEGER,
                veredito     TEXT,
                distancia_km REAL,
                ocr_texto    TEXT,
                data_criacao TEXT
            )
        """)
        conn.commit()


def imagem_ja_existe(hash_imagem: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT id FROM analises WHERE hash_imagem = ?", (hash_imagem,)
        ).fetchone()
        return row is not None


def salvar_analise(hash_imagem, endereco, score_risco, veredito, distancia_km, ocr_texto):
    with sqlite3.connect(DB_PATH) as conn:
        try:
            conn.execute(
                """
                INSERT INTO analises
                    (hash_imagem, endereco, score_risco, veredito, distancia_km, ocr_texto, data_criacao)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (hash_imagem, endereco, score_risco, veredito, distancia_km,
                 ocr_texto, datetime.now().isoformat()),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass


def buscar_historico():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            SELECT id, hash_imagem, endereco, score_risco, veredito,
                   distancia_km, ocr_texto, data_criacao
            FROM analises
            ORDER BY data_criacao DESC
            LIMIT 100
            """
        )
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]
