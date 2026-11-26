import pytest

from cors import origenes_permitidos


@pytest.mark.parametrize("valor", [None, ""])
def test_sin_variable_se_permiten_los_origenes_de_la_aplicacion(monkeypatch, valor):
    if valor is None:
        monkeypatch.delenv("ORIGENES_PERMITIDOS", raising=False)
    else:
        monkeypatch.setenv("ORIGENES_PERMITIDOS", valor)
    assert origenes_permitidos() == ["http://localhost:5173", "null"]


def test_la_variable_reemplaza_la_lista_e_ignora_espacios(monkeypatch):
    monkeypatch.setenv("ORIGENES_PERMITIDOS", " https://ejemplo.com , null,")
    assert origenes_permitidos() == ["https://ejemplo.com", "null"]
