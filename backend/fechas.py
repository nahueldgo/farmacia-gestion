from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

ZONA = ZoneInfo("America/Argentina/Buenos_Aires")


# El servidor va en UTC (3 h adelantado): después de las 21:00 marcaría el día siguiente.
def hoy() -> date:
    return datetime.now(ZONA).date()


# Hora actual de Argentina, con zona: para mostrar o para decidir de qué día es algo.
def ahora() -> datetime:
    return datetime.now(ZONA)


# Lo que se guarda en la base: hora UTC sin zona, como las columnas TIMESTAMP.
def ahora_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# Pasa una hora guardada en la base (UTC) a la hora de Argentina.
def a_hora_argentina(guardada: datetime) -> datetime:
    return guardada.replace(tzinfo=timezone.utc).astimezone(ZONA)


# Rango UTC [inicio, fin) que ocupa un día de Argentina: para "las ventas del día" y el cierre de caja.
def rango_utc_del_dia(dia: date) -> tuple[datetime, datetime]:
    inicio = datetime.combine(dia, time.min, tzinfo=ZONA)
    fin = datetime.combine(dia + timedelta(days=1), time.min, tzinfo=ZONA)
    return (
        inicio.astimezone(timezone.utc).replace(tzinfo=None),
        fin.astimezone(timezone.utc).replace(tzinfo=None),
    )
