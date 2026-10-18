import { useEffect, useState, type FormEvent } from 'react';
import { API_URL } from '../config/api';

interface Props {
  token: string;
  alCrear: () => void;
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

const TIPOS = [
  { valor: 'medicamento', etiqueta: 'Medicamento' },
  { valor: 'perfumeria', etiqueta: 'Perfumería' },
  { valor: 'cuidado_personal', etiqueta: 'Cuidado personal' },
  { valor: 'otro', etiqueta: 'Otro' },
];

function etiquetaIva(c: CondicionIva) {
  return Number(c.alicuota) === 0 ? 'Exento' : `${c.alicuota}%`;
}

export function FormularioProducto({ token, alCrear, alCancelar }: Props) {
  const [nombre, setNombre] = useState('');
  const [descripcion, setDescripcion] = useState('');
  const [tipo, setTipo] = useState('');
  const [precio, setPrecio] = useState('');
  const [condicionIvaId, setCondicionIvaId] = useState('');
  const [laboratorioId, setLaboratorioId] = useState('');
  const [stockMinimo, setStockMinimo] = useState('');

  const [condicionesIva, setCondicionesIva] = useState<CondicionIva[]>([]);
  const [laboratorios, setLaboratorios] = useState<Laboratorio[]>([]);
  const [cargandoCatalogos, setCargandoCatalogos] = useState(true);

  const [error, setError] = useState('');
  const [enviando, setEnviando] = useState(false);

  // Al abrir el formulario, traemos las listas de IVA y laboratorios
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

  const esMedicamento = tipo === 'medicamento';

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    setError('');

    if (!nombre.trim() || !tipo || !precio || !condicionIvaId) {
      setError('Completá el nombre, el tipo, el precio y la condición de IVA.');
      return;
    }
    const precioNumero = Number(precio);
    if (Number.isNaN(precioNumero) || precioNumero <= 0) {
      setError('El precio tiene que ser un número mayor a 0.');
      return;
    }
    if (esMedicamento && !laboratorioId) {
      setError('Un medicamento necesita laboratorio.');
      return;
    }
    if (stockMinimo !== '') {
      const minimo = Number(stockMinimo);
      if (!Number.isInteger(minimo) || minimo < 0) {
        setError('El stock mínimo tiene que ser un número entero, 0 o mayor.');
        return;
      }
    }

    const cuerpo: Record<string, unknown> = {
      nombre: nombre.trim(),
      tipo_producto: tipo,
      precio: precioNumero,
      condicion_iva_id: Number(condicionIvaId),
    };
    if (descripcion.trim()) cuerpo.descripcion = descripcion.trim();
    if (laboratorioId) cuerpo.laboratorio_id = Number(laboratorioId);
    if (stockMinimo !== '') cuerpo.stock_minimo = Number(stockMinimo);

    setEnviando(true);
    try {
      const respuesta = await fetch(`${API_URL}/productos`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(cuerpo),
      });
      if (respuesta.status === 401) {
        setError('Tu sesión venció. Volvé a iniciar sesión.');
      } else if (respuesta.status === 403) {
        setError('No tenés permiso para crear productos.');
      } else if (!respuesta.ok) {
        let mensaje = 'No se pudo crear el producto.';
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

  if (cargandoCatalogos) return <p>Cargando formulario...</p>;

  return (
    <form onSubmit={enviar} style={{ margin: '16px 0' }}>
      <h3>Nuevo producto</h3>
      <div>
        <label>
          Nombre:{' '}
          <input value={nombre} onChange={(e) => setNombre(e.target.value)} />
        </label>
      </div>
      <div>
        <label>
          Descripción (opcional):{' '}
          <input value={descripcion} onChange={(e) => setDescripcion(e.target.value)} />
        </label>
      </div>
      <div>
        <label>
          Tipo:{' '}
          <select value={tipo} onChange={(e) => setTipo(e.target.value)}>
            <option value="">— Elegir —</option>
            {TIPOS.map((t) => (
              <option key={t.valor} value={t.valor}>{t.etiqueta}</option>
            ))}
          </select>
        </label>
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
            <option value="">— Elegir —</option>
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
          Laboratorio {esMedicamento ? '(obligatorio)' : '(opcional)'}:{' '}
          <select value={laboratorioId} onChange={(e) => setLaboratorioId(e.target.value)}>
            <option value="">— Ninguno —</option>
            {laboratorios.map((l) => (
              <option key={l.id_laboratorio} value={l.id_laboratorio}>
                {l.nombre}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div>
        <label>
          Stock mínimo (opcional):{' '}
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
        {enviando ? 'Guardando...' : 'Guardar producto'}
      </button>{' '}
      <button type="button" onClick={alCancelar}>Cancelar</button>
    </form>
  );
}