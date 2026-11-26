import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react';
import { API_URL } from '../config/api';
import { useAuth } from '../context/AuthContext';
import { ListadoVentas } from '../components/ListadoVentas';

interface Producto {
  id_producto: number;
  nombre: string;
  descripcion: string | null;
  laboratorio_id: number | null;
  precio: number;
  condicion_iva_id: number;
  tipo_producto: string;
  stock_minimo: number | null;
  activo: boolean;
  stock: number;
}

interface LineaCarrito {
  producto: Producto;
  cantidad: number;
}

const MEDIOS_PAGO = [
  { valor: 'efectivo', etiqueta: 'Efectivo' },
  { valor: 'tarjeta_credito', etiqueta: 'Tarjeta de crédito' },
  { valor: 'tarjeta_debito', etiqueta: 'Tarjeta de débito' },
  { valor: 'transferencia', etiqueta: 'Transferencia' },
  { valor: 'qr', etiqueta: 'QR' },
];

function formatearMonto(valor: number) {
  return valor.toLocaleString('es-AR', { style: 'currency', currency: 'ARS' });
}

// El backend manda "detail" como texto o como lista (errores 422)
function mensajeDeError(datos: unknown, porDefecto: string) {
  const detail = (datos as { detail?: unknown })?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && typeof detail[0]?.msg === 'string') return detail[0].msg;
  return porDefecto;
}

export function Ventas() {
  const { usuario } = useAuth();
  const token = usuario?.token;
  const puedeVender = usuario?.rol !== 'dueno';

  const [productos, setProductos] = useState<Producto[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');
  const [busqueda, setBusqueda] = useState('');
  const [termino, setTermino] = useState('');
  const [carrito, setCarrito] = useState<LineaCarrito[]>([]);

  const [medioPago, setMedioPago] = useState('efectivo');
  const [enviando, setEnviando] = useState(false);
  const [errorVenta, setErrorVenta] = useState('');
  const [ventaOk, setVentaOk] = useState('');

  // Se suma después de cada venta para que el listado se vuelva a pedir
  const [versionVentas, setVersionVentas] = useState(0);

  // Clave que identifica el pedido: si se reintenta el mismo pedido por un corte
  // de conexión, el backend no duplica la venta. Se renueva si cambia el carrito.
  const claveRef = useRef<string | null>(null);

  useEffect(() => {
    claveRef.current = null;
  }, [carrito, medioPago]);

  const cargar = useCallback(async () => {
    if (!token) return;
    setCargando(true);
    setError('');
    try {
      const parametros = termino ? `?buscar=${encodeURIComponent(termino)}` : '';
      const respuesta = await fetch(`${API_URL}/productos${parametros}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (respuesta.status === 401) {
        setError('Tu sesión venció. Volvé a iniciar sesión.');
      } else if (respuesta.status === 403) {
        setError('No tenés permiso para ver los productos.');
      } else if (!respuesta.ok) {
        setError('No se pudieron cargar los productos.');
      } else {
        setProductos(await respuesta.json());
      }
    } catch {
      setError('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setCargando(false);
    }
  }, [token, termino]);

  useEffect(() => {
    cargar();
  }, [cargar]);

  function buscar(evento: FormEvent) {
    evento.preventDefault();
    setTermino(busqueda.trim());
  }

  function limpiarBusqueda() {
    setBusqueda('');
    setTermino('');
  }

  function agregar(producto: Producto) {
    setVentaOk('');
    setErrorVenta('');
    setCarrito((actual) => {
      const existente = actual.find((l) => l.producto.id_producto === producto.id_producto);
      if (existente) {
        // No dejamos pasar el stock disponible
        if (existente.cantidad >= producto.stock) return actual;
        return actual.map((l) =>
          l.producto.id_producto === producto.id_producto
            ? { ...l, cantidad: l.cantidad + 1 }
            : l
        );
      }
      return [...actual, { producto, cantidad: 1 }];
    });
  }

  function cambiarCantidad(idProducto: number, cambio: number) {
    setCarrito((actual) =>
      actual
        .map((l) => {
          if (l.producto.id_producto !== idProducto) return l;
          // No dejamos pasar el stock disponible
          return { ...l, cantidad: Math.min(l.cantidad + cambio, l.producto.stock) };
        })
        .filter((l) => l.cantidad > 0)
    );
  }

  function quitar(idProducto: number) {
    setCarrito((actual) => actual.filter((l) => l.producto.id_producto !== idProducto));
  }

  function vaciarCarrito() {
    setCarrito([]);
  }

  async function confirmarVenta() {
    if (carrito.length === 0) return;
    setErrorVenta('');
    setVentaOk('');
    if (!claveRef.current) claveRef.current = crypto.randomUUID();

    setEnviando(true);
    try {
      const respuesta = await fetch(`${API_URL}/ventas`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          medio_pago: medioPago,
          lineas: carrito.map((l) => ({
            producto_id: l.producto.id_producto,
            cantidad: l.cantidad,
          })),
          clave_operacion: claveRef.current,
        }),
      });
      if (respuesta.status === 401) {
        setErrorVenta('Tu sesión venció. Volvé a iniciar sesión.');
      } else if (respuesta.status === 403) {
        setErrorVenta('No tenés permiso para registrar ventas.');
      } else if (!respuesta.ok) {
        let datos: unknown = null;
        try {
          datos = await respuesta.json();
        } catch {
          // si la respuesta no es JSON, usamos el mensaje por defecto
        }
        setErrorVenta(mensajeDeError(datos, 'No se pudo registrar la venta.'));
        cargar();
      } else {
        const venta = await respuesta.json();
        setVentaOk(
          `Venta ${venta.numero_comprobante} registrada. Total cobrado: ${formatearMonto(venta.total_a_pagar)}.`
        );
        setCarrito([]);
        setMedioPago('efectivo');
        cargar();
        setVersionVentas((v) => v + 1);
      }
    } catch {
      setErrorVenta(
        'No se pudo conectar con el servidor. Revisá tu conexión y volvé a confirmar: la venta no se duplica.'
      );
    } finally {
      setEnviando(false);
    }
  }

  const total = carrito.reduce((suma, l) => suma + l.producto.precio * l.cantidad, 0);

  if (!puedeVender) {
    return (
      <div>
        <h2>Ventas</h2>
        <p>Tu rol solo puede consultar las ventas.</p>
        {token && <ListadoVentas token={token} version={versionVentas} puedeAnular={false} />}
      </div>
    );
  }

  return (
    <div>
      <h2>Ventas</h2>
      <div style={{ display: 'flex', gap: '32px', alignItems: 'flex-start' }}>
        <div style={{ flex: 2 }}>
          <form onSubmit={buscar} style={{ marginBottom: '12px' }}>
            <input
              placeholder="Buscar por nombre"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
            />{' '}
            <button type="submit">Buscar</button>
            {termino && (
              <>
                {' '}
                <button type="button" onClick={limpiarBusqueda}>
                  Ver todos
                </button>
              </>
            )}
          </form>

          {error ? (
            <p style={{ color: 'crimson' }}>
              {error} <button onClick={cargar}>Reintentar</button>
            </p>
          ) : cargando ? (
            <p>Cargando...</p>
          ) : productos.length === 0 ? (
            <p>No se encontraron productos.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Producto</th>
                  <th>Precio</th>
                  <th>Stock</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {productos.map((p) => (
                  <tr key={p.id_producto}>
                    <td>{p.nombre}</td>
                    <td>{formatearMonto(p.precio)}</td>
                    <td>{p.stock}</td>
                    <td>
                      <button onClick={() => agregar(p)} disabled={p.stock <= 0}>
                        Agregar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div style={{ flex: 1 }}>
          <h3>Carrito</h3>
          {ventaOk && <p style={{ color: 'green' }}>{ventaOk}</p>}
          {errorVenta && <p style={{ color: 'crimson' }}>{errorVenta}</p>}
          {carrito.length === 0 ? (
            <p>El carrito está vacío.</p>
          ) : (
            <div>
              <ul style={{ paddingLeft: '18px' }}>
                {carrito.map((l) => (
                  <li key={l.producto.id_producto} style={{ marginBottom: '8px' }}>
                    {l.producto.nombre}: {formatearMonto(l.producto.precio * l.cantidad)}
                    <div>
                      <button onClick={() => cambiarCantidad(l.producto.id_producto, -1)}>-</button>{' '}
                      {l.cantidad}{' '}
                      <button
                        onClick={() => cambiarCantidad(l.producto.id_producto, 1)}
                        disabled={l.cantidad >= l.producto.stock}
                      >
                        +
                      </button>{' '}
                      <button onClick={() => quitar(l.producto.id_producto)}>Quitar</button>
                    </div>
                  </li>
                ))}
              </ul>
              <p>
                <strong>Total: {formatearMonto(total)}</strong>
              </p>
              <div style={{ marginBottom: '12px' }}>
                <label>
                  Medio de pago:{' '}
                  <select value={medioPago} onChange={(e) => setMedioPago(e.target.value)}>
                    {MEDIOS_PAGO.map((m) => (
                      <option key={m.valor} value={m.valor}>
                        {m.etiqueta}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <button onClick={confirmarVenta} disabled={enviando}>
                {enviando ? 'Registrando...' : 'Confirmar venta'}
              </button>{' '}
              <button onClick={vaciarCarrito} disabled={enviando}>
                Vaciar carrito
              </button>
            </div>
          )}
        </div>
      </div>

        {token && <ListadoVentas token={token} version={versionVentas} puedeAnular={true} />}
    </div>
  );
}