import { useCallback, useEffect, useState } from 'react';
import { API_URL } from '../config/api';

interface AlertaStockBajo {
  id_producto: number;
  nombre: string;
  stock: number;
  stock_minimo: number;
  faltante: number;
}

interface AlertaVencimiento {
  id_lote: number;
  producto_id: number;
  producto: string;
  numero_lote: string;
  fecha_vencimiento: string;
  cantidad: number;
  dias_restantes: number;
  estado: 'vencido' | 'por_vencer';
}

interface Props {
  token: string;
}

const OPCIONES_DIAS = [7, 15, 30, 60, 90];

// "2026-11-20" -> "20/11/2026"
function formatearFecha(iso: string) {
  const [anio, mes, dia] = iso.split('-');
  return `${dia}/${mes}/${anio}`;
}

function textoEstado(a: AlertaVencimiento) {
  if (a.estado === 'vencido') {
    const hace = Math.abs(a.dias_restantes);
    return `Vencido hace ${hace} ${hace === 1 ? 'día' : 'días'}`;
  }
  if (a.dias_restantes === 0) return 'Vence hoy';
  return `Vence en ${a.dias_restantes} ${a.dias_restantes === 1 ? 'día' : 'días'}`;
}

export function PanelAlertas({ token }: Props) {
  const [stockBajo, setStockBajo] = useState<AlertaStockBajo[]>([]);
  const [vencimientos, setVencimientos] = useState<AlertaVencimiento[]>([]);
  const [dias, setDias] = useState(30);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');
  const [abierto, setAbierto] = useState(false);

  const cargar = useCallback(async () => {
    setCargando(true);
    setError('');
    try {
      const cabeceras = { Authorization: `Bearer ${token}` };
      const [respStock, respVenc] = await Promise.all([
        fetch(`${API_URL}/alertas/stock-bajo`, { headers: cabeceras }),
        fetch(`${API_URL}/alertas/vencimientos?dias=${dias}`, { headers: cabeceras }),
      ]);
      if (respStock.status === 401 || respVenc.status === 401) {
        setError('Tu sesión venció. Volvé a iniciar sesión.');
      } else if (respStock.status === 403 || respVenc.status === 403) {
        setError('No tenés permiso para ver las alertas.');
      } else if (!respStock.ok || !respVenc.ok) {
        setError('No se pudieron cargar las alertas.');
      } else {
        setStockBajo(await respStock.json());
        setVencimientos(await respVenc.json());
      }
    } catch {
      setError('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setCargando(false);
    }
  }, [token, dias]);

  useEffect(() => {
    cargar();
  }, [cargar]);

  const vencidos = vencimientos.filter((a) => a.estado === 'vencido').length;
  const porVencer = vencimientos.length - vencidos;

  return (
    <div style={{ border: '1px solid #ccc', padding: '12px', marginBottom: '16px' }}>
      <strong>Alertas</strong>{' '}
      {error ? (
        <span style={{ color: 'crimson' }}>
          {error} <button onClick={cargar}>Reintentar</button>
        </span>
      ) : cargando ? (
        <span>Cargando...</span>
      ) : stockBajo.length === 0 && vencimientos.length === 0 ? (
        <span>Sin alertas. Todo en orden.</span>
      ) : (
        <>
          <span>
            {stockBajo.length} {stockBajo.length === 1 ? 'producto' : 'productos'} con stock bajo ·{' '}
            {vencidos} {vencidos === 1 ? 'lote vencido' : 'lotes vencidos'} · {porVencer}{' '}
            {porVencer === 1 ? 'lote por vencer' : 'lotes por vencer'}
          </span>{' '}
          <button onClick={() => setAbierto(!abierto)}>
            {abierto ? 'Ocultar detalle' : 'Ver detalle'}
          </button>{' '}
          <button onClick={cargar}>Actualizar</button>
        </>
      )}

      {abierto && !error && !cargando && (
        <div style={{ marginTop: 12 }}>
          <h4>Stock bajo</h4>
          {stockBajo.length === 0 ? (
            <p>No hay productos por debajo del mínimo.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Producto</th>
                  <th>Stock</th>
                  <th>Mínimo</th>
                  <th>Faltan</th>
                </tr>
              </thead>
              <tbody>
                {stockBajo.map((a) => (
                  <tr key={a.id_producto}>
                    <td>{a.nombre}</td>
                    <td style={{ color: 'crimson', fontWeight: 'bold' }}>{a.stock}</td>
                    <td>{a.stock_minimo}</td>
                    <td>{a.faltante}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <h4>
            Lotes vencidos o que vencen en{' '}
            <select value={dias} onChange={(e) => setDias(Number(e.target.value))}>
              {OPCIONES_DIAS.map((d) => (
                <option key={d} value={d}>
                  {d} días
                </option>
              ))}
            </select>
          </h4>
          {vencimientos.length === 0 ? (
            <p>No hay lotes vencidos ni por vencer en ese plazo.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Producto</th>
                  <th>Lote</th>
                  <th>Vencimiento</th>
                  <th>Cantidad</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {vencimientos.map((a) => (
                  <tr key={a.id_lote}>
                    <td>{a.producto}</td>
                    <td>{a.numero_lote}</td>
                    <td>{formatearFecha(a.fecha_vencimiento)}</td>
                    <td>{a.cantidad}</td>
                    <td
                      style={{
                        color: a.estado === 'vencido' || a.dias_restantes === 0 ? 'crimson' : 'darkorange',
                      }}
                    >
                      {textoEstado(a)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}