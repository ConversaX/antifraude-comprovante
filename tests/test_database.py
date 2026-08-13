import os
import tempfile

import database


def test_database_create_and_insert(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setenv('DATABASE_URL', str(db_file))
    # reload module variables
    import importlib
    importlib.reload(database)

    database.criar_tabelas()
    database.salvar_analise('hash1', 'phash1', 'Rua A', 10, 'Aprovado', 0.0, 'texto')
    hist = database.buscar_historico()
    assert len(hist) >= 1
