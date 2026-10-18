import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { API_URL } from '../config/api';
import { useAuth } from '../context/AuthContext';
import { FormularioLote } from '../components/FormularioLote';

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

interface Lote {
  id_lote: number;
  producto_id: number;
  numero_lote: string;
  fecha_vencimiento: string;
  cantidad: number;
  fecha_creacion: string;
}

function formatearPrecio(valor: number) {
  return Number(valor).toLocaleString('es-AR', { style: 'currency', currency: 'ARS' });
}

// "2026-11-20" -> "20/11/2026"
function formatearFecha(iso: string) {
  const [anio, mes, dia] = iso.split('-');
  return `${dia}/${mes}/${anio}`;
}

// Días que faltan para el vencimiento (negativo si ya venció)
function diasHasta(iso: string) {
  const [anio, mes, dia] = iso.split('-').map(Number);
  const vencimiento = new Date(anio, mes - 1, dia);
  const hoy = new Date();
  hoy.setHours(0, 0, 0, 0);
  return Math.round((vencimiento.getTime() - hoy.getTime()) / 86400000);
}

function estadoVencimiento(iso: string) {
  const dias = diasHasta(iso);
  if (dias < 0) return { texto: 'Vencido', color: 'crimson' };
  if (dias === 0) return { texto: 'Vence hoy', color: 'crimson' };
  const texto = `Vence en ${dias} ${dias === 1 ? 'día' : 'días'}`;
  return { texto, color: dias <= 30 ? 'darkorange' : 'inherit' };
}

export function Stock() {
  const { usuario } = useAuth();
  const token = usuario?.token;

  // Listado de productos
  const [productos, setProductos] = useState<Producto[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');
  const [busqueda, setBusqueda] = useState('');
  const [termino, setTermino] = useState('');

  // Detalle de lotes
  const [seleccionado, setSeleccionado] = useState<Producto | null>(null);
  const [lotes, setLotes] = useState<Lote[]>([]);
  const [cargandoLotes, setCargandoLotes] = useState(false);
  const [errorLotes, setErrorLotes] = useState('');
  const [incluirAgotados, setIncluirAgotados] = useState(false);
  const [mostrarAlta, setMostrarAlta] = useState(false);
  
  // Solo farmaceutico y auxiliar pueden cargar lotes (el dueño recibe 403)
  const puedeAgregarLote = usuario?.rol === 'farmaceutico' || usuario?.rol === 'auxiliar';

  const cargar = useCallback(async () => {
    if (!token) return;
    setCargando(true);
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
        setError('No se pudo cargar el listado de productos.');
      } else {
        setProductos(await respuesta.json());
        setError('');
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

  const cargarLotes = useCallback(async () => {
    if (!token || !seleccionado) return;
    setCargandoLotes(true);
    try {
      const parametros = incluirAgotados ? '?incluir_agotados=true' : '';
      const respuesta = await fetch(
        `${API_URL}/productos/${seleccionado.id_producto}/lotes${parametros}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!respuesta.ok) {
        setErrorLotes('No se pudieron cargar los lotes.');
      } else {
        setLotes(await respuesta.json());
        setErrorLotes('');
      }
    } catch {
      setErrorLotes('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setCargandoLotes(false);
    }
  }, [token, seleccionado, incluirAgotados]);

  useEffect(() => {
    cargarLotes();
  }, [cargarLotes]);

  function buscar(evento: FormEvent) {
    evento.preventDefault();
    setTermino(busqueda.trim());
  }

  function limpiar() {
    setBusqueda('');
    setTermino('');
  }

  function verLotes(producto: Producto) {
    setSeleccionado(producto);
    setLotes([]);
    setErrorLotes('');
    setMostrarAlta(false);
  }

  if (error) return <p style={{ color: 'crimson' }}>{error}</p>;

  return (
    <div>
      <h2>Stock</h2>

      <form onSubmit={buscar} style={{ marginBottom: 16 }}>
        <input
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          placeholder="Buscar por nombre"
        />{' '}
        <button type="submit">Buscar</button>{' '}
        {termino && <button type="button" onClick={limpiar}>Limpiar</button>}
      </form>

      {cargando ? (
        <p>Cargando productos...</p>
      ) : productos.length === 0 ? (
        <p>
          {termino
            ? `No hay productos que coincidan con "${termino}".`
            : 'Todavía no hay productos cargados.'}
        </p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Producto</th>
              <th>Tipo</th>
              <th>Precio</th>
              <th>Stock</th>
              <th>Stock mínimo</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {productos.map((p) => {
              const bajo = p.stock < (p.stock_minimo ?? 0);
              return (
                <tr key={p.id_producto}>
                  <td>{p.nombre}</td>
                  <td>{p.tipo_producto}</td>
                  <td>{formatearPrecio(p.precio)}</td>
                  <td style={bajo ? { color: 'crimson', fontWeight: 'bold' } : undefined}>
                    {p.stock}{bajo && ' (stock bajo)'}
                  </td>
                  <td>{p.stock_minimo ?? '-'}</td>
                  <td>
                    <button onClick={() => verLotes(p)}>Ver lotes</button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}

      {seleccionado && (
        <div style={{ marginTop: 32 }}>
          <h3>Lotes de {seleccionado.nombre}</h3>
          <label>
            <input
              type="checkbox"
              checked={incluirAgotados}
              onChange={(e) => setIncluirAgotados(e.target.checked)}
            />{' '}
            Mostrar lotes agotados
          </label>{' '}
          <button onClick={() => setSeleccionado(null)}>Cerrar</button>
          {puedeAgregarLote && !mostrarAlta && (
            <>
              {' '}
              <button onClick={() => setMostrarAlta(true)}>Agregar lote</button>
            </>
          )}

          {mostrarAlta && token && (
            <FormularioLote
              token={token}
              idProducto={seleccionado.id_producto}
              alCrear={() => {
                setMostrarAlta(false);
                cargarLotes();
                cargar();
              }}
              alCancelar={() => setMostrarAlta(false)}
            />
          )}

          {errorLotes ? (
            <p style={{ color: 'crimson' }}>{errorLotes}</p>
          ) : cargandoLotes ? (
            <p>Cargando lotes...</p>
          ) : lotes.length === 0 ? (
            <p>Este producto no tiene lotes con stock.</p>
          ) : (
            <table style={{ marginTop: 12 }}>
              <thead>
                <tr>
                  <th>Lote</th>
                  <th>Vencimiento</th>
                  <th>Cantidad</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {lotes.map((l) => {
                  const estado = estadoVencimiento(l.fecha_vencimiento);
                  return (
                    <tr key={l.id_lote}>
                      <td>{l.numero_lote}</td>
                      <td>{formatearFecha(l.fecha_vencimiento)}</td>
                      <td>{l.cantidad}</td>
                      <td style={{ color: estado.color }}>{estado.texto}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}