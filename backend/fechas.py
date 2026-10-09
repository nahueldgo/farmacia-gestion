from datetime import date, datetime
from zoneinfo import ZoneInfo

ZONA = ZoneInfo("America/Argentina/Buenos_Aires")


# El servidor va en UTC (3 h adelantado): después de las 21:00 marcaría el día siguiente.
def hoy() -> date:
    return datetime.now(ZONA).date()