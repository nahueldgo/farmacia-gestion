import { useCallback, useEffect, useState } from 'react';
import { API_URL } from '../config/api';

interface VentaResumen {
  id_venta: number;
  numero_comprobante: string;
  fecha: string;
  empleado: string;
  medio_pago: string;
  total_a_pagar: number;
  estado: string;
}

interface Props {
  token: string;
  // Cuando cambia este número, el listado se vuelve a pedir (por ejemplo, después de vender)
  version: number;
  // Solo farmaceutico y auxiliar anulan (el backend le responde 403 al dueño)
  puedeAnular: boolean;
}

function formatearMonto(valor: number) {
  return Number(valor).toLocaleString('es-AR', { style: 'currency', currency: 'ARS' });
}

function formatearFechaHora(iso: string) {
  return new Date(iso).toLocaleString('es-AR', { hourCycle: 'h23' });
}

function nombreMedioPago(medio: string) {
  return medio.replace('_', ' ');
}

export function ListadoVentas({ token, version, puedeAnular }: Props) {
  const [ventas, setVentas] = useState<VentaResumen[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');

  // Lo que se escribe en los campos, y el rango ya aplicado ('' = solo las de hoy)
  const [desdeEscrito, setDesdeEscrito] = useState('');
  const [hastaEscrito, setHastaEscrito] = useState('');
  const [rango, setRango] = useState<{ desde: string; hasta: string }>({ desde: '', hasta: '' });

  // Anulación con confirmación en la página
  const [ventaAAnular, setVentaAAnular] = useState<VentaResumen | null>(null);
  const [anulando, setAnulando] = useState(false);
  const [errorAnular, setErrorAnular] = useState('');

  const cargar = useCallback(async () => {
    setCargando(true);
    try {
      const parametros = new URLSearchParams();
      if (rango.desde) parametros.set('desde', rango.desde);
      if (rango.hasta) parametros.set('hasta', rango.hasta);
      const consulta = parametros.toString() ? `?${parametros.toString()}` : '';
      const respuesta = await fetch(`${API_URL}/ventas${consulta}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (respuesta.status === 401) {
        setError('Tu sesión venció. Volvé a iniciar sesión.');
      } else if (respuesta.status === 403) {
        setError('No tenés permiso para ver las ventas.');
      } else if (!respuesta.ok) {
        let mensaje = 'No se pudo cargar el listado de ventas.';
        try {
          const datos = await respuesta.json();
          if (typeof datos.detail === 'string') mensaje = datos.detail;
        } catch {
          // si la respuesta no es JSON, dejamos el mensaje por defecto
        }
        setError(mensaje);
      } else {
        setVentas(await respuesta.json());
        setError('');
      }
    } catch {
      setError('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setCargando(false);
    }
  }, [token, rango]);

  useEffect(() => {
    cargar();
  }, [cargar, version]);

  function aplicarRango() {
    // Si se completa una sola fecha, se busca ese día
    const desde = desdeEscrito || hastaEscrito;
    const hasta = hastaEscrito || desdeEscrito;
    setRango({ desde, hasta });
  }

  function volverAHoy() {
    setDesdeEscrito('');
    setHastaEscrito('');
    setRango({ desde: '', hasta: '' });
  }

  async function anularVenta() {
    if (!ventaAAnular) return;
    setAnulando(true);
    setErrorAnular('');
    try {
      const respuesta = await fetch(`${API_URL}/ventas/${ventaAAnular.id_venta}/anular`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (respuesta.status === 401) {
        setErrorAnular('Tu sesión venció. Volvé a iniciar sesión.');
      } else if (respuesta.status === 403) {
        setErrorAnular('No tenés permiso para anular ventas.');
      } else if (!respuesta.ok) {
        let mensaje = 'No se pudo anular la venta.';
        try {
          const datos = await respuesta.json();
          if (typeof datos.detail === 'string') mensaje = datos.detail;
        } catch {
          // si la respuesta no es JSON, dejamos el mensaje por defecto
        }
        setErrorAnular(mensaje);
      } else {
        setVentaAAnular(null);
        cargar();
      }
    } catch {
      setErrorAnular('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setAnulando(false);
    }
  }

  const esHoy = !rango.desde && !rango.hasta;

  return (
    <div style={{ marginTop: 32 }}>
      <h3>{esHoy ? 'Ventas de hoy' : 'Ventas del período'}</h3>

      <p>
        <label>
          Desde:{' '}
          <input type="date" value={desdeEscrito} onChange={(e) => setDesdeEscrito(e.target.value)} />
        </label>{' '}
        <label>
          Hasta:{' '}
          <input type="date" value={hastaEscrito} onChange={(e) => setHastaEscrito(e.target.value)} />
        </label>{' '}
        <button onClick={aplicarRango} disabled={!desdeEscrito && !hastaEscrito}>
          Ver
        </button>{' '}
        {!esHoy && <button onClick={volverAHoy}>Volver a hoy</button>}
      </p>

      {ventaAAnular && (
        <div style={{ margin: '16px 0' }}>
          <p>
            ¿Anular la venta <strong>{ventaAAnular.numero_comprobante}</strong> por{' '}
            {formatearMonto(ventaAAnular.total_a_pagar)}? La venta pasa a "anulada" y no se borra.
            El stock <strong>no se devuelve</strong> a los lotes: si hace falta, el farmacéutico lo
            corrige desde Stock con "Ajustar", y la devolución del dinero se registra en Caja como
            un retiro con su motivo.
          </p>
          {errorAnular && <p style={{ color: 'crimson' }}>{errorAnular}</p>}
          <button onClick={anularVenta} disabled={anulando}>
            {anulando ? 'Anulando...' : 'Sí, anular'}
          </button>{' '}
          <button onClick={() => setVentaAAnular(null)} disabled={anulando}>
            Cancelar
          </button>
        </div>
      )}

      {error ? (
        <p style={{ color: 'crimson' }}>
          {error} <button onClick={cargar}>Reintentar</button>
        </p>
      ) : cargando ? (
        <p>Cargando ventas...</p>
      ) : ventas.length === 0 ? (
        <p>{esHoy ? 'Todavía no hay ventas hoy.' : 'No hay ventas en ese período.'}</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Comprobante</th>
              <th>Fecha y hora</th>
              <th>Empleado</th>
              <th>Medio de pago</th>
              <th>Total</th>
              <th>Estado</th>
              {puedeAnular && <th>Acciones</th>}
            </tr>
          </thead>
          <tbody>
            {ventas.map((v) => (
              <tr key={v.id_venta}>
                <td>{v.numero_comprobante}</td>
                <td>{formatearFechaHora(v.fecha)}</td>
                <td>{v.empleado}</td>
                <td>{nombreMedioPago(v.medio_pago)}</td>
                <td>{formatearMonto(v.total_a_pagar)}</td>
                <td style={v.estado === 'anulada' ? { color: 'crimson' } : undefined}>
                  {v.estado === 'anulada' ? 'Anulada' : 'Confirmada'}
                </td>
                {puedeAnular && (
                  <td>
                    {v.estado === 'confirmada' && (
                      <button
                        onClick={() => {
                          setErrorAnular('');
                          setVentaAAnular(v);
                        }}
                      >
                        Anular
                      </button>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}