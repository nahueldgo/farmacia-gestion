import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { API_URL } from '../config/api';
import { useAuth } from '../context/AuthContext';

interface ConsolidadoCaja {
  caja: {
    id_caja: number;
    hora_apertura: string;
    monto_apertura: number;
    estado: string;
  };
  efectivo_esperado: number;
}

function formatearMonto(valor: number) {
  return valor.toLocaleString('es-AR', { style: 'currency', currency: 'ARS' });
}

function formatearFechaHora(iso: string) {
  return new Date(iso).toLocaleString('es-AR', { hourCycle: 'h23' });
}

// El backend manda "detail" como texto o como lista (errores 422)
function mensajeDeError(datos: unknown, porDefecto: string) {
  const detail = (datos as { detail?: unknown })?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && typeof detail[0]?.msg === 'string') return detail[0].msg;
  return porDefecto;
}

export function Caja() {
  const { usuario } = useAuth();
  const token = usuario?.token;
  const puedeAbrir = usuario?.rol !== 'dueno';

  const [consolidado, setConsolidado] = useState<ConsolidadoCaja | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');

  const [monto, setMonto] = useState('');
  const [errorAbrir, setErrorAbrir] = useState('');
  const [abriendo, setAbriendo] = useState(false);

  const cargar = useCallback(async () => {
    if (!token) return;
    setCargando(true);
    setError('');
    try {
      const respuesta = await fetch(`${API_URL}/caja/actual/consolidado`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (respuesta.status === 404) {
        setConsolidado(null);
      } else if (respuesta.status === 401) {
        setError('Tu sesión venció. Volvé a iniciar sesión.');
      } else if (respuesta.status === 403) {
        setError('No tenés permiso para ver la caja.');
      } else if (!respuesta.ok) {
        setError('No se pudo cargar la caja.');
      } else {
        setConsolidado(await respuesta.json());
      }
    } catch {
      setError('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setCargando(false);
    }
  }, [token]);

  useEffect(() => {
    cargar();
  }, [cargar]);

  async function abrirCaja(evento: FormEvent) {
    evento.preventDefault();
    setErrorAbrir('');

    const valor = Number(monto);
    if (monto.trim() === '' || Number.isNaN(valor) || valor < 0) {
      setErrorAbrir('Ingresá un monto inicial válido (0 o mayor).');
      return;
    }

    setAbriendo(true);
    try {
      const respuesta = await fetch(`${API_URL}/caja/abrir`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ monto_apertura: valor }),
      });
      if (respuesta.status === 401) {
        setErrorAbrir('Tu sesión venció. Volvé a iniciar sesión.');
      } else if (respuesta.status === 403) {
        setErrorAbrir('No tenés permiso para abrir la caja.');
      } else if (!respuesta.ok) {
        let datos: unknown = null;
        try {
          datos = await respuesta.json();
        } catch {
          // si la respuesta no es JSON, usamos el mensaje por defecto
        }
        setErrorAbrir(mensajeDeError(datos, 'No se pudo abrir la caja.'));
        // Si ya había una caja abierta (409), la mostramos
        if (respuesta.status === 409) cargar();
      } else {
        setMonto('');
        cargar();
      }
    } catch {
      setErrorAbrir('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setAbriendo(false);
    }
  }

  return (
    <div>
      <h2>Caja</h2>
      {error ? (
        <p style={{ color: 'crimson' }}>
          {error} <button onClick={cargar}>Reintentar</button>
        </p>
      ) : cargando ? (
        <p>Cargando...</p>
      ) : !consolidado ? (
        puedeAbrir ? (
          <form onSubmit={abrirCaja}>
            <p>No hay una caja abierta. Abrila para empezar a vender.</p>
            <div>
              <label>
                Monto inicial:{' '}
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={monto}
                  onChange={(e) => setMonto(e.target.value)}
                />
              </label>
            </div>
            {errorAbrir && <p style={{ color: 'crimson' }}>{errorAbrir}</p>}
            <button type="submit" disabled={abriendo}>
              {abriendo ? 'Abriendo...' : 'Abrir caja'}
            </button>
          </form>
        ) : (
          <p>No hay una caja abierta.</p>
        )
      ) : (
        <div>
          <p>
            <strong>Caja abierta</strong> el {formatearFechaHora(consolidado.caja.hora_apertura)}
          </p>
          <p>Monto inicial: {formatearMonto(consolidado.caja.monto_apertura)}</p>
          <p>Efectivo esperado: {formatearMonto(consolidado.efectivo_esperado)}</p>
        </div>
      )}
    </div>
  );
}