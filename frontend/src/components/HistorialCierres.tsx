import { useCallback, useEffect, useState } from 'react';
import { API_URL } from '../config/api';
import { ResumenCaja, type ConsolidadoCaja } from './ResumenCaja';

interface Cierre {
  id_caja: number;
  fecha: string;
  hora_apertura: string;
  hora_cierre: string | null;
  monto_apertura: number;
  monto_cierre_declarado: number | null;
  monto_cierre_sistema: number | null;
  diferencia: number | null;
  empleado_apertura: string;
  empleado_cierre: string;
}

function formatearMonto(valor: number) {
  return valor.toLocaleString('es-AR', { style: 'currency', currency: 'ARS' });
}

function formatearFechaHora(iso: string) {
  return new Date(iso).toLocaleString('es-AR', { hourCycle: 'h23' });
}

// "2026-11-19" -> "19/11/2026"
function formatearFecha(fecha: string) {
  const [anio, mes, dia] = fecha.split('-');
  return `${dia}/${mes}/${anio}`;
}

function textoDiferencia(diferencia: number | null) {
  if (diferencia === null) return '-';
  if (diferencia === 0) return 'Sin diferencia';
  return diferencia > 0
    ? `Sobrante ${formatearMonto(diferencia)}`
    : `Faltante ${formatearMonto(Math.abs(diferencia))}`;
}

export function HistorialCierres({ token }: { token: string }) {
  const [desde, setDesde] = useState('');
  const [hasta, setHasta] = useState('');
  // Lo que se está consultando: las fechas se aplican al tocar "Ver"
  const [consulta, setConsulta] = useState({ desde: '', hasta: '' });

  const [cierres, setCierres] = useState<Cierre[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');

  const [detalle, setDetalle] = useState<ConsolidadoCaja | null>(null);
  const [cargandoDetalle, setCargandoDetalle] = useState(false);
  const [errorDetalle, setErrorDetalle] = useState('');

  const cargar = useCallback(async () => {
    setCargando(true);
    setError('');
    try {
      // Con una sola fecha el backend devuelve ese día; con las dos, todo el rango
      const primera = consulta.desde || consulta.hasta;
      const parametros = new URLSearchParams();
      if (primera) parametros.set('desde', primera);
      if (consulta.desde && consulta.hasta) parametros.set('hasta', consulta.hasta);
      const texto = parametros.toString();

      const respuesta = await fetch(`${API_URL}/caja/cierres${texto ? `?${texto}` : ''}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (respuesta.status === 401) {
        setError('Tu sesión venció. Volvé a iniciar sesión.');
      } else if (!respuesta.ok) {
        let mensaje = 'No se pudo cargar el historial de cierres.';
        try {
          const datos = await respuesta.json();
          if (typeof datos.detail === 'string') mensaje = datos.detail;
          else if (Array.isArray(datos.detail) && datos.detail[0]?.msg) mensaje = datos.detail[0].msg;
        } catch {
          // si la respuesta no es JSON, dejamos el mensaje por defecto
        }
        setError(mensaje);
      } else {
        setCierres(await respuesta.json());
      }
    } catch {
      setError('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setCargando(false);
    }
  }, [token, consulta]);

  useEffect(() => {
    cargar();
  }, [cargar]);

  function ver() {
    if (desde && hasta && hasta < desde) {
      setError('La fecha "hasta" no puede ser anterior a "desde".');
      return;
    }
    setDetalle(null);
    setConsulta({ desde, hasta });
  }

  function volverAHoy() {
    setDesde('');
    setHasta('');
    setDetalle(null);
    setConsulta({ desde: '', hasta: '' });
  }

  async function verDetalle(idCaja: number) {
    setErrorDetalle('');
    setCargandoDetalle(true);
    try {
      const respuesta = await fetch(`${API_URL}/caja/${idCaja}/consolidado`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (respuesta.status === 401) {
        setErrorDetalle('Tu sesión venció. Volvé a iniciar sesión.');
      } else if (!respuesta.ok) {
        setErrorDetalle('No se pudo cargar el detalle del cierre.');
      } else {
        setDetalle(await respuesta.json());
      }
    } catch {
      setErrorDetalle('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setCargandoDetalle(false);
    }
  }

  const hayFiltro = consulta.desde !== '' || consulta.hasta !== '';

  return (
    <div style={{ marginTop: '32px' }}>
      <h3>Historial de cierres</h3>
      <p>
        <label>
          Desde:{' '}
          <input type="date" value={desde} onChange={(e) => setDesde(e.target.value)} />
        </label>{' '}
        <label>
          Hasta:{' '}
          <input type="date" value={hasta} onChange={(e) => setHasta(e.target.value)} />
        </label>{' '}
        <button onClick={ver}>Ver</button>{' '}
        {hayFiltro && <button onClick={volverAHoy}>Volver a hoy</button>}
      </p>
      <p style={{ color: 'gray' }}>
        {hayFiltro ? 'Cierres del período elegido.' : 'Cierres de hoy.'}
      </p>

      {error ? (
        <p style={{ color: 'crimson' }}>{error}</p>
      ) : cargando ? (
        <p>Cargando...</p>
      ) : cierres.length === 0 ? (
        <p>No hay cierres en este período.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Abrió</th>
              <th>Cerró</th>
              <th>Cierre</th>
              <th>Declarado</th>
              <th>Esperado</th>
              <th>Diferencia</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {cierres.map((c) => (
              <tr key={c.id_caja}>
                <td>{formatearFecha(c.fecha)}</td>
                <td>{c.empleado_apertura}</td>
                <td>{c.empleado_cierre}</td>
                <td>{c.hora_cierre ? formatearFechaHora(c.hora_cierre) : '-'}</td>
                <td>
                  {c.monto_cierre_declarado !== null
                    ? formatearMonto(c.monto_cierre_declarado)
                    : '-'}
                </td>
                <td>
                  {c.monto_cierre_sistema !== null ? formatearMonto(c.monto_cierre_sistema) : '-'}
                </td>
                <td
                  style={{
                    color: c.diferencia === 0 ? 'green' : c.diferencia === null ? undefined : 'crimson',
                  }}
                >
                  {textoDiferencia(c.diferencia)}
                </td>
                <td>
                  <button onClick={() => verDetalle(c.id_caja)} disabled={cargandoDetalle}>
                    Ver detalle
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {errorDetalle && <p style={{ color: 'crimson' }}>{errorDetalle}</p>}
      {detalle && (
        <div style={{ border: '1px solid gray', padding: 12, margin: '16px 0' }}>
          <p>
            <button onClick={() => setDetalle(null)}>Cerrar detalle</button>
          </p>
          <ResumenCaja consolidado={detalle} />
        </div>
      )}
    </div>
  );
}