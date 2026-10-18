import { useState, type FormEvent } from 'react';
import { API_URL } from '../config/api';

interface Props {
  token: string;
  idProducto: number;
  alCrear: () => void;
  alCancelar: () => void;
}

export function FormularioLote({ token, idProducto, alCrear, alCancelar }: Props) {
  const [numeroLote, setNumeroLote] = useState('');
  const [fechaVencimiento, setFechaVencimiento] = useState('');
  const [cantidad, setCantidad] = useState('');
  const [error, setError] = useState('');
  const [enviando, setEnviando] = useState(false);

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    setError('');

    if (!numeroLote.trim() || !fechaVencimiento || !cantidad) {
      setError('Completá el número de lote, el vencimiento y la cantidad.');
      return;
    }
    const cantidadNumero = Number(cantidad);
    if (!Number.isInteger(cantidadNumero) || cantidadNumero <= 0) {
      setError('La cantidad tiene que ser un número entero mayor a 0.');
      return;
    }
    const hoy = new Date().toLocaleDateString('en-CA');
    if (fechaVencimiento < hoy) {
      setError('No se puede cargar un lote que ya está vencido.');
      return;
    }

    setEnviando(true);
    try {
      const respuesta = await fetch(`${API_URL}/productos/${idProducto}/lotes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          numero_lote: numeroLote.trim(),
          fecha_vencimiento: fechaVencimiento,
          cantidad: cantidadNumero,
        }),
      });
      if (respuesta.status === 401) {
        setError('Tu sesión venció. Volvé a iniciar sesión.');
      } else if (respuesta.status === 403) {
        setError('No tenés permiso para cargar lotes.');
      } else if (!respuesta.ok) {
        let mensaje = 'No se pudo crear el lote.';
        try {
          const datos = await respuesta.json();
          if (typeof datos.detail === 'string') mensaje = datos.detail;
        } catch {
          // si la respuesta no es JSON, dejamos el mensaje por defecto
        }
        setError(mensaje);
      } else {
        alCrear();
      }
    } catch {
      setError('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form onSubmit={enviar} style={{ margin: '16px 0' }}>
      <h4>Nuevo lote</h4>
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
      <div>
        <label>
          Cantidad:{' '}
          <input
            type="number"
            min="1"
            value={cantidad}
            onChange={(e) => setCantidad(e.target.value)}
          />
        </label>
      </div>
      {error && <p style={{ color: 'crimson' }}>{error}</p>}
      <button type="submit" disabled={enviando}>
        {enviando ? 'Guardando...' : 'Guardar lote'}
      </button>{' '}
      <button type="button" onClick={alCancelar}>Cancelar</button>
    </form>
  );
}