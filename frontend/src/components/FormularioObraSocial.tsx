import { useState, type FormEvent } from 'react';
import { API_URL } from '../config/api';

export interface ObraSocialEditable {
  id_obra_social: number;
  nombre: string;
  cuit: string | null;
  contacto: string | null;
  tipo_validacion: string;
}

interface Props {
  token: string;
  actual: ObraSocialEditable | null; // null = alta, con datos = edición
  alGuardar: () => void;
  alCancelar: () => void;
}

const TIPOS_VALIDACION = [
  { valor: 'manual', etiqueta: 'Manual' },
  { valor: 'externa', etiqueta: 'Externa' },
];

export function FormularioObraSocial({ token, actual, alGuardar, alCancelar }: Props) {
  const [nombre, setNombre] = useState(actual?.nombre ?? '');
  const [cuit, setCuit] = useState(actual?.cuit ?? '');
  const [contacto, setContacto] = useState(actual?.contacto ?? '');
  const [tipoValidacion, setTipoValidacion] = useState(actual?.tipo_validacion ?? 'manual');

  const [error, setError] = useState('');
  const [enviando, setEnviando] = useState(false);

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    setError('');

    if (!nombre.trim()) {
      setError('El nombre no puede quedar vacío.');
      return;
    }
    // Aceptamos el CUIT con guiones o espacios y lo mandamos solo con los 11 números
    const cuitLimpio = cuit.replace(/[-\s]/g, '');
    if (cuitLimpio && !/^\d{11}$/.test(cuitLimpio)) {
      setError('El CUIT tiene que tener 11 números.');
      return;
    }

    let metodo = 'POST';
    let ruta = '/obras-sociales';
    const cuerpo: Record<string, string | null> = {};

    if (!actual) {
      cuerpo.nombre = nombre.trim();
      if (cuitLimpio) cuerpo.cuit = cuitLimpio;
      if (contacto.trim()) cuerpo.contacto = contacto.trim();
      cuerpo.tipo_validacion = tipoValidacion;
    } else {
      // En la edición mandamos solo lo que cambió; el CUIT y el contacto se pueden vaciar
      metodo = 'PATCH';
      ruta = `/obras-sociales/${actual.id_obra_social}`;
      if (nombre.trim() !== actual.nombre) cuerpo.nombre = nombre.trim();
      if (cuitLimpio !== (actual.cuit ?? '')) cuerpo.cuit = cuitLimpio || null;
      if (contacto.trim() !== (actual.contacto ?? '')) cuerpo.contacto = contacto.trim() || null;
      if (tipoValidacion !== actual.tipo_validacion) cuerpo.tipo_validacion = tipoValidacion;
      if (Object.keys(cuerpo).length === 0) {
        setError('No cambiaste ningún dato.');
        return;
      }
    }

    setEnviando(true);
    try {
      const respuesta = await fetch(`${API_URL}${ruta}`, {
        method: metodo,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(cuerpo),
      });
      if (respuesta.status === 401) {
        setError('Tu sesión venció. Volvé a iniciar sesión.');
      } else if (respuesta.status === 403) {
        setError('No tenés permiso para configurar obras sociales.');
      } else if (!respuesta.ok) {
        let mensaje = 'No se pudo guardar la obra social.';
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
      <h3>{actual ? `Editar ${actual.nombre}` : 'Nueva obra social'}</h3>
      <div>
        <label>
          Nombre:{' '}
          <input value={nombre} onChange={(e) => setNombre(e.target.value)} />
        </label>
      </div>
      <div>
        <label>
          CUIT (opcional):{' '}
          <input
            value={cuit}
            onChange={(e) => setCuit(e.target.value)}
            placeholder="11 números"
          />
        </label>
      </div>
      <div>
        <label>
          Contacto (opcional):{' '}
          <input value={contacto} onChange={(e) => setContacto(e.target.value)} />
        </label>
      </div>
      <div>
        <label>
          Validación:{' '}
          <select value={tipoValidacion} onChange={(e) => setTipoValidacion(e.target.value)}>
            {TIPOS_VALIDACION.map((t) => (
              <option key={t.valor} value={t.valor}>
                {t.etiqueta}
              </option>
            ))}
          </select>
        </label>
      </div>
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