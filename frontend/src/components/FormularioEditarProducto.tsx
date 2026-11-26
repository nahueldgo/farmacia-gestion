import { useEffect, useState, type FormEvent } from 'react';
import { API_URL } from '../config/api';
import { NuevoCatalogo } from './NuevoCatalogo';

interface ProductoEditable {
  id_producto: number;
  nombre: string;
  descripcion: string | null;
  laboratorio_id: number | null;
  precio: number;
  condicion_iva_id: number;
  tipo_producto: string;
  stock_minimo: number | null;
}

interface Props {
  token: string;
  producto: ProductoEditable;
  alGuardar: () => void;
  alCancelar: () => void;
}

interface CondicionIva {
  id_condicion_iva: number;
  nombre: string;
  alicuota: number;
}

interface Laboratorio {
  id_laboratorio: number;
  nombre: string;
  activo: boolean;
}

function etiquetaIva(c: CondicionIva) {
  return Number(c.alicuota) === 0 ? 'Exento' : `${c.alicuota}%`;
}

export function FormularioEditarProducto({ token, producto, alGuardar, alCancelar }: Props) {
  const [nombre, setNombre] = useState(producto.nombre);
  const [descripcion, setDescripcion] = useState(producto.descripcion ?? '');
  const [precio, setPrecio] = useState(String(producto.precio));
  const [condicionIvaId, setCondicionIvaId] = useState(String(producto.condicion_iva_id));
  const [laboratorioId, setLaboratorioId] = useState(
    producto.laboratorio_id ? String(producto.laboratorio_id) : ''
  );
  const [stockMinimo, setStockMinimo] = useState(String(producto.stock_minimo ?? 0));

  const [condicionesIva, setCondicionesIva] = useState<CondicionIva[]>([]);
  const [laboratorios, setLaboratorios] = useState<Laboratorio[]>([]);
  const [cargandoCatalogos, setCargandoCatalogos] = useState(true);

  const [error, setError] = useState('');
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    async function cargarCatalogos() {
      try {
        const cabeceras = { Authorization: `Bearer ${token}` };
        const [respIva, respLab] = await Promise.all([
          fetch(`${API_URL}/catalogos/condiciones-iva`, { headers: cabeceras }),
          fetch(`${API_URL}/catalogos/laboratorios`, { headers: cabeceras }),
        ]);
        if (!respIva.ok || !respLab.ok) {
          setError('No se pudieron cargar las listas de IVA y laboratorios.');
        } else {
          setCondicionesIva(await respIva.json());
          const todos: Laboratorio[] = await respLab.json();
          setLaboratorios(todos.filter((l) => l.activo));
        }
      } catch {
        setError('No se pudo conectar con el servidor. Revisá tu conexión.');
      } finally {
        setCargandoCatalogos(false);
      }
    }
    cargarCatalogos();
  }, [token]);

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    setError('');

    if (!nombre.trim()) {
      setError('El nombre no puede quedar vacío.');
      return;
    }
    const precioNumero = Number(precio);
    if (precio === '' || Number.isNaN(precioNumero) || precioNumero <= 0) {
      setError('El precio tiene que ser un número mayor a 0.');
      return;
    }
    const minimo = Number(stockMinimo);
    if (stockMinimo === '' || !Number.isInteger(minimo) || minimo < 0) {
      setError('El stock mínimo tiene que ser un número entero, 0 o mayor.');
      return;
    }

    // Solo mandamos lo que cambió
    const cambios: Record<string, unknown> = {};
    if (nombre.trim() !== producto.nombre) cambios.nombre = nombre.trim();
    if (descripcion.trim() !== (producto.descripcion ?? '') && descripcion.trim()) {
      cambios.descripcion = descripcion.trim();
    }
    if (precioNumero !== Number(producto.precio)) cambios.precio = precioNumero;
    if (Number(condicionIvaId) !== producto.condicion_iva_id) {
      cambios.condicion_iva_id = Number(condicionIvaId);
    }
    if (laboratorioId && Number(laboratorioId) !== producto.laboratorio_id) {
      cambios.laboratorio_id = Number(laboratorioId);
    }
    if (minimo !== (producto.stock_minimo ?? 0)) cambios.stock_minimo = minimo;

    if (Object.keys(cambios).length === 0) {
      setError('No cambiaste ningún dato.');
      return;
    }

    setEnviando(true);
    try {
      const respuesta = await fetch(`${API_URL}/productos/${producto.id_producto}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(cambios),
      });
      if (respuesta.status === 401) {
        setError('Tu sesión venció. Volvé a iniciar sesión.');
      } else if (respuesta.status === 403) {
        setError('No tenés permiso para editar productos.');
      } else if (!respuesta.ok) {
        let mensaje = 'No se pudo guardar el producto.';
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

  if (cargandoCatalogos) return <p>Cargando formulario...</p>;

  return (
    <form onSubmit={enviar} style={{ margin: '16px 0' }}>
      <h3>Editar producto</h3>
      <div>
        <label>
          Nombre:{' '}
          <input value={nombre} onChange={(e) => setNombre(e.target.value)} />
        </label>
      </div>
      <div>
        <label>
          Descripción:{' '}
          <input value={descripcion} onChange={(e) => setDescripcion(e.target.value)} />
        </label>
      </div>
      <div>
        Tipo: {producto.tipo_producto} (no se puede cambiar)
      </div>
      <div>
        <label>
          Precio:{' '}
          <input
            type="number"
            min="0"
            step="0.01"
            value={precio}
            onChange={(e) => setPrecio(e.target.value)}
          />
        </label>
      </div>
      <div>
        <label>
          IVA:{' '}
          <select value={condicionIvaId} onChange={(e) => setCondicionIvaId(e.target.value)}>
            {condicionesIva.map((c) => (
              <option key={c.id_condicion_iva} value={c.id_condicion_iva}>
                {etiquetaIva(c)}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div>
        <label>
          Laboratorio:{' '}
          <select value={laboratorioId} onChange={(e) => setLaboratorioId(e.target.value)}>
            <option value="">— Ninguno —</option>
            {laboratorios.map((l) => (
              <option key={l.id_laboratorio} value={l.id_laboratorio}>
                {l.nombre}
              </option>
            ))}
          </select>
        </label>{' '}
        <NuevoCatalogo
          token={token}
          ruta="laboratorios"
          campoId="id_laboratorio"
          etiqueta="laboratorio"
          alCrear={(nuevo) => {
            setLaboratorios((previos) =>
              [...previos, { id_laboratorio: nuevo.id, nombre: nuevo.nombre, activo: true }].sort(
                (a, b) => a.nombre.localeCompare(b.nombre)
              )
            );
            setLaboratorioId(String(nuevo.id));
          }}
        />
      </div>
      <div>
        <label>
          Stock mínimo:{' '}
          <input
            type="number"
            min="0"
            value={stockMinimo}
            onChange={(e) => setStockMinimo(e.target.value)}
          />
        </label>
      </div>
      {error && <p style={{ color: 'crimson' }}>{error}</p>}
      <button type="submit" disabled={enviando}>
        {enviando ? 'Guardando...' : 'Guardar cambios'}
      </button>{' '}
      <button type="button" onClick={alCancelar} disabled={enviando}>
        Cancelar
      </button>
    </form>
  );
}