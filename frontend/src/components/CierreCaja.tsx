import { useState } from 'react';
import { API_URL } from '../config/api';
import type { ConsolidadoCaja } from './ResumenCaja';

interface Props {
  token: string;
  alCerrar: (consolidadoFinal: ConsolidadoCaja) => void;
}

function mensajeDeError(datos: unknown, porDefecto: string) {
  const detail = (datos as { detail?: unknown })?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && typeof detail[0]?.msg === 'string') return detail[0].msg;
  return porDefecto;
}

export function CierreCaja({ token, alCerrar }: Props) {
  const [abierto, setAbierto] = useState(false);
  const [monto, setMonto] = useState('');
  const [error, setError] = useState('');
  const [enviando, setEnviando] = useState(false);

  function cancelar() {
    setAbierto(false);
    setMonto('');
    setError('');
  }

  async function cerrar() {
    setError('');

    // Aceptamos la coma como separador decimal
    const montoTexto = monto.trim().replace(',', '.');
    if (!/^\d+(\.\d{1,2})?$/.test(montoTexto)) {
      setError('Ingresá el efectivo contado (0 o mayor, con hasta 2 decimales).');
      return;
    }
    if (Number(montoTexto) > 99999999.99) {
      setError('El monto es demasiado grande.');
      return;
    }

    setEnviando(true);
    try {
      const respuesta = await fetch(`${API_URL}/caja/cerrar`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ monto_declarado: Number(montoTexto) }),
      });
      if (respuesta.status === 401) {
        setError('Tu sesión venció. Volvé a iniciar sesión.');
      } else if (respuesta.status === 403) {
        setError('No tenés permiso para cerrar la caja.');
      } else if (!respuesta.ok) {
        let datos: unknown = null;
        try {
          datos = await respuesta.json();
        } catch {
          // si la respuesta no es JSON, usamos el mensaje por defecto
        }
        setError(mensajeDeError(datos, 'No se pudo cerrar la caja.'));
      } else {
        alCerrar(await respuesta.json());
      }
    } catch {
      setError('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setEnviando(false);
    }
  }

  if (!abierto) {
    return (
      <p>
        <button onClick={() => setAbierto(true)}>Cerrar caja</button>
      </p>
    );
  }

  return (
    <div style={{ border: '1px solid crimson', padding: 12, margin: '16px 0' }}>
      <h3>Cerrar caja</h3>
      <p>
        Contá el efectivo que hay en la caja e ingresalo. El cierre no se puede deshacer: para
        seguir vendiendo vas a tener que abrir otra caja.
      </p>
      <div>
        <label>
          Efectivo contado:{' '}
          <input
            value={monto}
            onChange={(e) => setMonto(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') cerrar();
            }}
            placeholder="0,00"
          />
        </label>
      </div>
      {error && <p style={{ color: 'crimson' }}>{error}</p>}
      <button onClick={cerrar} disabled={enviando}>
        {enviando ? 'Cerrando...' : 'Confirmar cierre'}
      </button>{' '}
      <button onClick={cancelar} disabled={enviando}>
        Cancelar
      </button>
    </div>
  );
}