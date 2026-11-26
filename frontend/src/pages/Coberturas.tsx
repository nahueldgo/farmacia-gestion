import { useCallback, useEffect, useState } from 'react';
import { API_URL } from '../config/api';
import { useAuth } from '../context/AuthContext';
import { FormularioObraSocial } from '../components/FormularioObraSocial';
import { PanelReglas } from '../components/PanelReglas';

interface ObraSocial {
  id_obra_social: number;
  nombre: string;
  cuit: string | null;
  contacto: string | null;
  tipo_validacion: string;
  activo: boolean;
}

// "30123456789" -> "30-12345678-9"
function formatearCuit(cuit: string | null) {
  if (!cuit) return '-';
  return cuit.length === 11 ? `${cuit.slice(0, 2)}-${cuit.slice(2, 10)}-${cuit.slice(10)}` : cuit;
}

function nombreValidacion(tipo: string) {
  return tipo === 'externa' ? 'Externa' : 'Manual';
}

export function Coberturas() {
  const { usuario } = useAuth();
  const token = usuario?.token;
  const esFarmaceutico = usuario?.rol === 'farmaceutico';

  const [obrasSociales, setObrasSociales] = useState<ObraSocial[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');
  const [mostrarAlta, setMostrarAlta] = useState(false);
  const [conReglas, setConReglas] = useState<ObraSocial | null>(null);
  const [editando, setEditando] = useState<ObraSocial | null>(null);
  const [confirmandoBaja, setConfirmandoBaja] = useState<ObraSocial | null>(null);
  const [errorAccion, setErrorAccion] = useState('');
  const [procesando, setProcesando] = useState(false);

  const cargar = useCallback(async () => {
    if (!token) return;
    setCargando(true);
    try {
      const respuesta = await fetch(`${API_URL}/obras-sociales?incluir_inactivas=true`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (respuesta.status === 401) {
        setError('Tu sesión venció. Volvé a iniciar sesión.');
      } else if (respuesta.status === 403) {
        setError('No tenés permiso para ver las obras sociales.');
      } else if (!respuesta.ok) {
        setError('No se pudo cargar el listado de obras sociales.');
      } else {
        setObrasSociales(await respuesta.json());
        setError('');
      }
    } catch {
      setError('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setCargando(false);
    }
  }, [token]);

  useEffect(() => {
    if (esFarmaceutico) cargar();
  }, [esFarmaceutico, cargar]);

  // Baja y reactivación: PATCH sin cuerpo
  async function cambiarEstado(obra: ObraSocial, accion: 'baja' | 'reactivar') {
    if (!token) return;
    setErrorAccion('');
    setProcesando(true);
    try {
      const respuesta = await fetch(`${API_URL}/obras-sociales/${obra.id_obra_social}/${accion}`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (respuesta.status === 401) {
        setErrorAccion('Tu sesión venció. Volvé a iniciar sesión.');
      } else if (respuesta.status === 403) {
        setErrorAccion('No tenés permiso para hacer esto.');
      } else if (!respuesta.ok) {
        let mensaje = 'No se pudo completar la acción.';
        try {
          const datos = await respuesta.json();
          if (typeof datos.detail === 'string') mensaje = datos.detail;
        } catch {
          // si la respuesta no es JSON, dejamos el mensaje por defecto
        }
        setErrorAccion(mensaje);
      } else {
        setConfirmandoBaja(null);
        cargar();
      }
    } catch {
      setErrorAccion('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setProcesando(false);
    }
  }

  if (!esFarmaceutico) {
    return (
      <div>
        <h2>Coberturas</h2>
        <p>Solo el farmacéutico configura las obras sociales y sus coberturas.</p>
      </div>
    );
  }

  return (
    <div>
      <h2>Configurar coberturas</h2>
      {!mostrarAlta && !editando && (
        <p>
          <button
            onClick={() => {
              setConReglas(null);
              setConfirmandoBaja(null);
              setMostrarAlta(true);
            }}
          >
            Nueva obra social
          </button>
        </p>
      )}

      {mostrarAlta && token && (
        <FormularioObraSocial
          token={token}
          actual={null}
          alGuardar={() => {
            setMostrarAlta(false);
            cargar();
          }}
          alCancelar={() => setMostrarAlta(false)}
        />
      )}

      {editando && token && (
        <FormularioObraSocial
          key={editando.id_obra_social}
          token={token}
          actual={editando}
          alGuardar={() => {
            setEditando(null);
            cargar();
          }}
          alCancelar={() => setEditando(null)}
        />
      )}

      {confirmandoBaja && (
        <div style={{ border: '1px solid crimson', padding: 12, margin: '12px 0' }}>
          <p>
            ¿Dar de baja a <strong>{confirmandoBaja.nombre}</strong>? Ya no se va a poder elegir en
            las ventas, pero no se pierden sus reglas ni las ventas anteriores. Se puede reactivar
            cuando quieras.
          </p>
          <button onClick={() => cambiarEstado(confirmandoBaja, 'baja')} disabled={procesando}>
            {procesando ? 'Procesando...' : 'Sí, dar de baja'}
          </button>{' '}
          <button onClick={() => setConfirmandoBaja(null)} disabled={procesando}>
            Cancelar
          </button>
        </div>
      )}

      {errorAccion && <p style={{ color: 'crimson' }}>{errorAccion}</p>}

      {error ? (
        <p style={{ color: 'crimson' }}>
          {error} <button onClick={cargar}>Reintentar</button>
        </p>
      ) : cargando ? (
        <p>Cargando obras sociales...</p>
      ) : obrasSociales.length === 0 ? (
        <p>Todavía no hay obras sociales cargadas.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Obra social</th>
              <th>CUIT</th>
              <th>Contacto</th>
              <th>Validación</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {obrasSociales.map((o) => (
              <tr key={o.id_obra_social}>
                <td style={o.activo ? undefined : { color: 'gray' }}>{o.nombre}</td>
                <td>{formatearCuit(o.cuit)}</td>
                <td>{o.contacto ?? '-'}</td>
                <td>{nombreValidacion(o.tipo_validacion)}</td>
                <td style={o.activo ? undefined : { color: 'gray' }}>
                  {o.activo ? 'Activa' : 'Dada de baja'}
                </td>
                <td>
                  <button
                    onClick={() => {
                      setMostrarAlta(false);
                      setEditando(null);
                      setConfirmandoBaja(null);
                      setConReglas(o);
                    }}
                  >
                    Reglas
                  </button>{' '}
                  <button
                    onClick={() => {
                      setMostrarAlta(false);
                      setConReglas(null);
                      setConfirmandoBaja(null);
                      setErrorAccion('');
                      setEditando(o);
                    }}
                  >
                    Editar
                  </button>{' '}
                  {o.activo ? (
                    <button
                      onClick={() => {
                        setErrorAccion('');
                        setEditando(null);
                        setConfirmandoBaja(o);
                      }}
                    >
                      Dar de baja
                    </button>
                  ) : (
                    <button onClick={() => cambiarEstado(o, 'reactivar')} disabled={procesando}>
                      Reactivar
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {conReglas && token && (
        <PanelReglas
          key={conReglas.id_obra_social}
          token={token}
          obraSocial={conReglas}
          alCerrar={() => setConReglas(null)}
        />
      )}
    </div>
  );
}