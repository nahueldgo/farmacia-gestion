import { useCallback, useEffect, useState } from 'react';
import { API_URL } from '../config/api';
import { useAuth } from '../context/AuthContext';
import { FormularioObraSocial } from '../components/FormularioObraSocial';

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
      {!mostrarAlta && (
        <p>
          <button onClick={() => setMostrarAlta(true)}>Nueva obra social</button>
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
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}