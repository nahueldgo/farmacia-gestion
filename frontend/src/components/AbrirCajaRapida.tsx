import { useState } from 'react';
import { API_URL } from '../config/api';

interface Props {
  token: string;
  alAbrir: () => void;
}

function mensajeDeError(datos: unknown, porDefecto: string) {
  const detail = (datos as { detail?: unknown })?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && typeof detail[0]?.msg === 'string') return detail[0].msg;
  return porDefecto;
}

export function AbrirCajaRapida({ token, alAbrir }: Props) {
  const [monto, setMonto] = useState('');
  const [error, setError] = useState('');
  const [enviando, setEnviando] = useState(false);

  async function abrir() {
    setError('');

    // Aceptamos la coma como separador decimal
    const montoTexto = monto.trim().replace(',', '.');
    if (!/^\d+(\.\d{1,2})?$/.test(montoTexto)) {
      setError('Ingresá un monto inicial válido (0 o mayor, con hasta 2 decimales).');
      return;
    }

    setEnviando(true);
    try {
      const respuesta = await fetch(`${API_URL}/caja/abrir`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ monto_apertura: Number(montoTexto) }),
      });
      if (respuesta.status === 401) {
        setError('Tu sesión venció. Volvé a iniciar sesión.');
      } else if (respuesta.status === 403) {
        setError('No tenés permiso para abrir la caja.');
      } else if (respuesta.status === 409) {
        // Ya había una caja abierta: se puede seguir vendiendo
        alAbrir();
      } else if (!respuesta.ok) {
        let datos: unknown = null;
        try {
          datos = await respuesta.json();
        } catch {
          // si la respuesta no es JSON, usamos el mensaje por defecto
        }
        setError(mensajeDeError(datos, 'No se pudo abrir la caja.'));
      } else {
        alAbrir();
      }
    } catch {
      setError('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div style={{ border: '1px solid gray', padding: 12, margin: '12px 0' }}>
      <p>Abrí la caja para poder vender. Tu carrito no se pierde.</p>
      <label>
        Monto inicial:{' '}
        <input
          value={monto}
          onChange={(e) => setMonto(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') abrir();
          }}
          placeholder="0,00"
        />
      </label>{' '}
      <button onClick={abrir} disabled={enviando}>
        {enviando ? 'Abriendo...' : 'Abrir caja'}
      </button>
      {error && <p style={{ color: 'crimson' }}>{error}</p>}
    </div>
  );
}