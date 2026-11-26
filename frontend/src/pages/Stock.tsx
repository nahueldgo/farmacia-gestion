import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { API_URL } from '../config/api';
import { useAuth } from '../context/AuthContext';
import { FormularioLote } from '../components/FormularioLote';
import { FormularioProducto } from '../components/FormularioProducto';
import { FormularioMedicamento, type DatosMedicamento } from '../components/FormularioMedicamento';
import { FormularioEditarProducto } from '../components/FormularioEditarProducto';
import { FormularioEditarLote } from '../components/FormularioEditarLote';
import { PanelAlertas } from '../components/PanelAlertas';

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

// Dias que faltan para el vencimiento (negativo si ya vencio)
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
  const [mostrarAltaProducto, setMostrarAltaProducto] = useState(false);

  // Datos de medicamento del producto seleccionado
  const [medicamento, setMedicamento] = useState<DatosMedicamento | null>(null);
  const [cargandoMed, setCargandoMed] = useState(false);
  const [errorMed, setErrorMed] = useState('');
  const [mostrarFormMed, setMostrarFormMed] = useState(false);

  const cargarMedicamento = useCallback(async () => {
    setMostrarFormMed(false);
    setErrorMed('');
    setMedicamento(null);
    if (!seleccionado || !token || seleccionado.tipo_producto !== 'medicamento') return;
    setCargandoMed(true);
    try {
      const respuesta = await fetch(`${API_URL}/productos/${seleccionado.id_producto}/medicamento`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (respuesta.status === 404) return; // todavía no tiene datos cargados
      if (respuesta.status === 401) {
        setErrorMed('Tu sesión venció. Volvé a iniciar sesión.');
        return;
      }
      if (!respuesta.ok) {
        setErrorMed('No se pudieron cargar los datos del medicamento.');
        return;
      }
      setMedicamento(await respuesta.json());
    } catch {
      setErrorMed('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setCargandoMed(false);
    }
  }, [seleccionado, token]);

  useEffect(() => {
    cargarMedicamento();
  }, [cargarMedicamento]);

  // Mismos permisos que para los lotes: farmaceutico y auxiliar
  const puedeAgregarProducto = puedeAgregarLote;

  // Solo el farmaceutico edita productos
  const puedeEditarProducto = usuario?.rol === 'farmaceutico';
  const [editando, setEditando] = useState<Producto | null>(null);

  // Solo el farmaceutico corrige o ajusta lotes
  const puedeEditarLote = usuario?.rol === 'farmaceutico';

  // Solo el farmaceutico ve las alertas (el resto recibe 403)
  const puedeVerAlertas = usuario?.rol === 'farmaceutico';

  const [loteEnEdicion, setLoteEnEdicion] = useState<{
    lote: Lote;
    modo: 'corregir' | 'ajustar';
  } | null>(null);

  // Retiro de lote (con confirmación en la página)
  const [loteARetirar, setLoteARetirar] = useState<Lote | null>(null);
  const [retirando, setRetirando] = useState(false);
  const [errorRetiro, setErrorRetiro] = useState('');

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
    setLoteEnEdicion(null);
    setLoteARetirar(null);
    setErrorRetiro('');
  }

  async function retirarLote() {
    if (!token || !loteARetirar) return;
    setRetirando(true);
    setErrorRetiro('');
    try {
      const respuesta = await fetch(`${API_URL}/lotes/${loteARetirar.id_lote}/retirar`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (respuesta.status === 401) {
        setErrorRetiro('Tu sesión venció. Volvé a iniciar sesión.');
      } else if (respuesta.status === 403) {
        setErrorRetiro('No tenés permiso para retirar lotes.');
      } else if (!respuesta.ok) {
        setErrorRetiro('No se pudo retirar el lote.');
      } else {
        setLoteARetirar(null);
        cargarLotes();
        cargar();
      }
    } catch {
      setErrorRetiro('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setRetirando(false);
    }
  }

  return (
    <div>
      <h2>Stock</h2>

      {puedeVerAlertas && token && <PanelAlertas token={token} />}
      {puedeAgregarProducto && !mostrarAltaProducto && (
        
        <p>
          <button onClick={() => setMostrarAltaProducto(true)}>Nuevo producto</button>
        </p>
      )}

      {mostrarAltaProducto && token && (
        <FormularioProducto
          token={token}
          alCrear={() => {
            setMostrarAltaProducto(false);
            cargar();
          }}
          alCancelar={() => setMostrarAltaProducto(false)}
        />
      )}

      {editando && token && (
        <FormularioEditarProducto
          key={editando.id_producto}
          token={token}
          producto={editando}
          alGuardar={() => {
            if (seleccionado?.id_producto === editando.id_producto) setSeleccionado(null);
            setEditando(null);
            cargar();
          }}
          alCancelar={() => setEditando(null)}
        />
      )}

      <form onSubmit={buscar} style={{ marginBottom: 16 }}>
        <input
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          placeholder="Buscar por nombre"
        />{' '}
        <button type="submit">Buscar</button>{' '}
        {termino && <button type="button" onClick={limpiar}>Limpiar</button>}
      </form>

      {error ? (
        <p style={{ color: 'crimson' }}>
          {error}{' '}
          <button onClick={cargar}>Reintentar</button>
        </p>
      ) : cargando ? (
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
                    {puedeEditarProducto && (
                      <>
                        {' '}
                        <button
                          onClick={() => {
                            setEditando(p);
                            window.scrollTo({ top: 0, behavior: 'smooth' });
                          }}
                        >
                          Editar
                        </button>
                      </>
                    )}
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

          {seleccionado.tipo_producto === 'medicamento' && (
            <div style={{ marginTop: 16 }}>
              <strong>Datos de medicamento: </strong>
              {cargandoMed ? (
                'Cargando...'
              ) : errorMed ? (
                <span style={{ color: 'crimson' }}>{errorMed}</span>
              ) : medicamento ? (
                `${medicamento.concentracion} · ${medicamento.requiere_receta ? 'Requiere receta' : 'Venta libre'}`
              ) : (
                'Sin datos cargados'
              )}
              {!cargandoMed &&
                !mostrarFormMed &&
                (medicamento ? usuario?.rol === 'farmaceutico' : puedeAgregarLote) && (
                  <>
                    {' '}
                    <button onClick={() => setMostrarFormMed(true)}>
                      {medicamento ? 'Editar datos' : 'Cargar datos'}
                    </button>
                  </>
                )}
            </div>
          )}

          {mostrarFormMed && token && (
            <FormularioMedicamento
              productoId={seleccionado.id_producto}
              productoNombre={seleccionado.nombre}
              token={token}
              actual={medicamento}
              onGuardado={cargarMedicamento}
              onCancelar={() => setMostrarFormMed(false)}
            />
          )}

          {loteEnEdicion && token && (
            <FormularioEditarLote
              key={`${loteEnEdicion.lote.id_lote}-${loteEnEdicion.modo}`}
              token={token}
              lote={loteEnEdicion.lote}
              modo={loteEnEdicion.modo}
              alGuardar={() => {
                setLoteEnEdicion(null);
                cargarLotes();
                cargar();
              }}
              alCancelar={() => setLoteEnEdicion(null)}
            />
          )}

          {loteARetirar && (
            <div style={{ margin: '16px 0' }}>
              <p>
                ¿Retirar el lote <strong>{loteARetirar.numero_lote}</strong>? Se van a descontar{' '}
                {loteARetirar.cantidad} unidades del stock. El lote no se borra: queda con cantidad 0.
              </p>
              {errorRetiro && <p style={{ color: 'crimson' }}>{errorRetiro}</p>}
              <button onClick={retirarLote} disabled={retirando}>
                {retirando ? 'Retirando...' : 'Sí, retirar'}
              </button>{' '}
              <button onClick={() => setLoteARetirar(null)} disabled={retirando}>
                Cancelar
              </button>
            </div>
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
                  {puedeEditarLote && <th>Acciones</th>}
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
                      {puedeEditarLote && (
                        <td>
                          <button onClick={() => setLoteEnEdicion({ lote: l, modo: 'corregir' })}>
                            Corregir
                          </button>{' '}
                          <button onClick={() => setLoteEnEdicion({ lote: l, modo: 'ajustar' })}>
                            Ajustar
                          </button>
                          {l.cantidad > 0 && (
                            <>
                              {' '}
                              <button
                                onClick={() => {
                                  setLoteEnEdicion(null);
                                  setErrorRetiro('');
                                  setLoteARetirar(l);
                                }}
                              >
                                Retirar
                              </button>
                            </>
                          )}
                        </td>
                      )}
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