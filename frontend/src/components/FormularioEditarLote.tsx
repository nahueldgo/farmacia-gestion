import { useState, type FormEvent } from 'react';
import { API_URL } from '../config/api';

interface LoteEditable {
  id_lote: number;
  numero_lote: string;
  fecha_vencimiento: string;
  cantidad: number;
}

interface Props {
  token: string;
  lote: LoteEditable;
  modo: 'corregir' | 'ajustar';
  alGuardar: () => void;
  alCancelar: () => void;
}

export function FormularioEditarLote({ token, lote, modo, alGuardar, alCancelar }: Props) {
  const [numeroLote, setNumeroLote] = useState(lote.numero_lote);
  const [fechaVencimiento, setFechaVencimiento] = useState(lote.fecha_vencimiento);
  const [cantidad, setCantidad] = useState(String(lote.cantidad));

  const [error, setError] = useState('');
  const [enviando, setEnviando] = useState(false);

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    setError('');

    let ruta = '';
    let cuerpo: Record<string, unknown> = {};

    if (modo === 'corregir') {
      if (!numeroLote.trim() || !fechaVencimiento) {
        setError('Completá el número de lote y la fecha de vencimiento.');
        return;
      }
      if (numeroLote.trim() !== lote.numero_lote) cuerpo.numero_lote = numeroLote.trim();
      if (fechaVencimiento !== lote.fecha_vencimiento) cuerpo.fecha_vencimiento = fechaVencimiento;
      if (Object.keys(cuerpo).length === 0) {
        setError('No cambiaste ningún dato.');
        return;
      }
      ruta = `/lotes/${lote.id_lote}`;
    } else {
      const nueva = Number(cantidad);
      if (cantidad === '' || !Number.isInteger(nueva) || nueva < 0) {
        setError('La cantidad tiene que ser un número entero, 0 o mayor.');
        return;
      }
      if (nueva === lote.cantidad) {
        setError('No cambiaste la cantidad.');
        return;
      }
      cuerpo = { cantidad: nueva };
      ruta = `/lotes/${lote.id_lote}/ajuste`;
    }

    setEnviando(true);
    try {
      const respuesta = await fetch(`${API_URL}${ruta}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(cuerpo),
      });
      if (respuesta.status === 401) {
        setError('Tu sesión venció. Volvé a iniciar sesión.');
      } else if (respuesta.status === 403) {
        setError('No tenés permiso para modificar lotes.');
      } else if (!respuesta.ok) {
        let mensaje = 'No se pudo guardar el lote.';
        try {
          const datos = await respuesta.json();
          if (typeof datos.detail === 'string') mensaje = datos.detail;
          else if (Array.isArray(datos.detail) && datos.detail[0]?.msg) mensaje = datos.detail[0].msg;
        } catch {
          // si la respuesta no es JSON, dejamos el mensaje por defecto
        }
        setError(mensaje);
      } else {
        alGuardar();
      }
    } catch {
      setError('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form onSubmit={enviar} style={{ margin: '16px 0' }}>
      <h4>
        {modo === 'corregir' ? 'Corregir lote' : 'Ajustar cantidad del lote'} {lote.numero_lote}
      </h4>
      {modo === 'corregir' ? (
        <>
          <div>
            <label>
              Número de lote:{' '}
              <input value={numeroLote} onChange={(e) => setNumeroLote(e.target.value)} />
            </label>
          </div>
          <div>
            <label>
              Vencimiento:{' '}
              <input
                type="date"
                value={fechaVencimiento}
                onChange={(e) => setFechaVencimiento(e.target.value)}
              />
            </label>
          </div>
        </>
      ) : (
        <div>
          <label>
            Cantidad:{' '}
            <input
              type="number"
              min="0"
              value={cantidad}
              onChange={(e) => setCantidad(e.target.value)}
            />
          </label>
        </div>
      )}
      {error && <p style={{ color: 'crimson' }}>{error}</p>}
      <button type="submit" disabled={enviando}>
        {enviando ? 'Guardando...' : 'Guardar'}
      </button>{' '}
      <button type="button" onClick={alCancelar} disabled={enviando}>
        Cancelar
      </button>
    </form>
  );
}