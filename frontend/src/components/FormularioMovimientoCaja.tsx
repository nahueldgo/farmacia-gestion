import { useState, type FormEvent } from 'react';
import { API_URL } from '../config/api';

interface Props {
  token: string;
  alRegistrar: () => void;
}

function mensajeDeError(datos: unknown, porDefecto: string) {
  const detail = (datos as { detail?: unknown })?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && typeof detail[0]?.msg === 'string') return detail[0].msg;
  return porDefecto;
}

export function FormularioMovimientoCaja({ token, alRegistrar }: Props) {
  const [tipo, setTipo] = useState('retiro');
  const [monto, setMonto] = useState('');
  const [motivo, setMotivo] = useState('');
  const [error, setError] = useState('');
  const [exito, setExito] = useState('');
  const [enviando, setEnviando] = useState(false);

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    setError('');
    setExito('');

    // Aceptamos la coma como separador decimal
    const montoTexto = monto.trim().replace(',', '.');
    if (!/^\d+(\.\d{1,2})?$/.test(montoTexto) || Number(montoTexto) <= 0) {
      setError('Ingresá un monto mayor a 0, con hasta 2 decimales.');
      return;
    }
    if (Number(montoTexto) > 99999999.99) {
      setError('El monto es demasiado grande.');
      return;
    }
    if (!motivo.trim()) {
      setError('El motivo es obligatorio.');
      return;
    }
    if (motivo.trim().length > 200) {
      setError('El motivo puede tener hasta 200 caracteres.');
      return;
    }

    setEnviando(true);
    try {
      const respuesta = await fetch(`${API_URL}/caja/movimientos`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          tipo,
          monto: Number(montoTexto),
          motivo: motivo.trim(),
        }),
      });
      if (respuesta.status === 401) {
        setError('Tu sesión venció. Volvé a iniciar sesión.');
      } else if (respuesta.status === 403) {
        setError('No tenés permiso para registrar movimientos.');
      } else if (!respuesta.ok) {
        let datos: unknown = null;
        try {
          datos = await respuesta.json();
        } catch {
          // si la respuesta no es JSON, usamos el mensaje por defecto
        }
        setError(mensajeDeError(datos, 'No se pudo registrar el movimiento.'));
      } else {
        setMonto('');
        setMotivo('');
        setExito(tipo === 'ingreso' ? 'Ingreso registrado.' : 'Retiro registrado.');
        alRegistrar();
      }
    } catch {
      setError('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form onSubmit={enviar} style={{ margin: '16px 0' }}>
      <h3>Registrar ingreso o retiro</h3>
      <div>
        <label>
          Tipo:{' '}
          <select value={tipo} onChange={(e) => setTipo(e.target.value)}>
            <option value="retiro">Retiro</option>
            <option value="ingreso">Ingreso</option>
          </select>
        </label>
      </div>
      <div>
        <label>
          Monto:{' '}
          <input value={monto} onChange={(e) => setMonto(e.target.value)} placeholder="0,00" />
        </label>
      </div>
      <div>
        <label>
          Motivo:{' '}
          <input
            value={motivo}
            onChange={(e) => setMotivo(e.target.value)}
            placeholder="Ej: devolución de la venta V-00000012"
            size={40}
          />
        </label>
      </div>
      {error && <p style={{ color: 'crimson' }}>{error}</p>}
      {exito && <p style={{ color: 'green' }}>{exito}</p>}
      <button type="submit" disabled={enviando}>
        {enviando ? 'Registrando...' : 'Registrar'}
      </button>
    </form>
  );
}