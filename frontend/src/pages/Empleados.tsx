import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { API_URL } from '../config/api';
import { useAuth } from '../context/AuthContext';

interface Empleado {
  id_empleado: number;
  nombre: string;
  apellido: string;
  dni: string;
  rol: string;
  matricula_profesional: string | null;
  fecha_ingreso: string;
  activo: boolean;
  nombre_usuario: string;
  email: string;
}

// Lee el mensaje de error que manda el backend (campo "detail"); si no hay, usa uno por defecto
async function leerDetalle(respuesta: Response, porDefecto: string) {
  const datos = await respuesta.json().catch(() => null);
  return typeof datos?.detail === 'string' ? datos.detail : porDefecto;
}

export function Empleados() {
  const { usuario } = useAuth();
  const token = usuario?.token;

  const [empleados, setEmpleados] = useState<Empleado[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');
  const [errorAccion, setErrorAccion] = useState('');
  const [mensaje, setMensaje] = useState('');
  const [enProceso, setEnProceso] = useState<number | null>(null);

  // Cambio de contraseña
  const [aCambiar, setACambiar] = useState<Empleado | null>(null);
  const [contrasenaNueva, setContrasenaNueva] = useState('');
  const [errorContrasena, setErrorContrasena] = useState('');
  const [guardando, setGuardando] = useState(false);

  const cargar = useCallback(async () => {
    if (!token) return;
    try {
      const respuesta = await fetch(`${API_URL}/empleados`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (respuesta.status === 401) {
        setError('Tu sesión venció. Volvé a iniciar sesión.');
      } else if (respuesta.status === 403) {
        setError('No tenés permiso para ver los empleados.');
      } else if (!respuesta.ok) {
        setError('No se pudo cargar la lista de empleados.');
      } else {
        setEmpleados(await respuesta.json());
        setError('');
      }
    } catch {
      setError('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setCargando(false);
    }
  }, [token]);

  useEffect(() => {
    cargar();
  }, [cargar]);

  async function cambiarEstado(empleado: Empleado, accion: 'baja' | 'reactivar') {
    if (
      accion === 'baja' &&
      !window.confirm(`¿Dar de baja a ${empleado.nombre} ${empleado.apellido}?`)
    ) {
      return;
    }
    setErrorAccion('');
    setMensaje('');
    setEnProceso(empleado.id_empleado);
    try {
      const respuesta = await fetch(
        `${API_URL}/empleados/${empleado.id_empleado}/${accion}`,
        { method: 'PATCH', headers: { Authorization: `Bearer ${token}` } }
      );
      if (!respuesta.ok) {
        setErrorAccion(await leerDetalle(respuesta, 'No se pudo completar la acción.'));
      } else {
        await cargar();
      }
    } catch {
      setErrorAccion('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setEnProceso(null);
    }
  }

  function abrirCambioContrasena(empleado: Empleado) {
    setACambiar(empleado);
    setContrasenaNueva('');
    setErrorContrasena('');
    setErrorAccion('');
    setMensaje('');
  }

  async function guardarContrasena(evento: FormEvent) {
    evento.preventDefault();
    if (!aCambiar) return;
    if (contrasenaNueva.length < 8) {
      setErrorContrasena('La contraseña debe tener al menos 8 caracteres.');
      return;
    }
    setErrorContrasena('');
    setGuardando(true);
    try {
      const respuesta = await fetch(
        `${API_URL}/empleados/${aCambiar.id_empleado}/contrasena`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ contrasena_nueva: contrasenaNueva }),
        }
      );
      if (!respuesta.ok) {
        setErrorContrasena(await leerDetalle(respuesta, 'No se pudo cambiar la contraseña.'));
      } else {
        setMensaje(
          `Contraseña de ${aCambiar.nombre} ${aCambiar.apellido} actualizada. Deberá cambiarla en su próximo ingreso.`
        );
        setACambiar(null);
        setContrasenaNueva('');
      }
    } catch {
      setErrorContrasena('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setGuardando(false);
    }
  }

  if (cargando) return <p>Cargando empleados...</p>;
  if (error) return <p style={{ color: 'crimson' }}>{error}</p>;

  return (
    <div>
      <h2>Empleados</h2>
      {mensaje && <p style={{ color: 'green' }}>{mensaje}</p>}
      {errorAccion && <p style={{ color: 'crimson' }}>{errorAccion}</p>}
      <table>
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Usuario</th>
            <th>Email</th>
            <th>Rol</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {empleados.map((e) => (
            <tr key={e.id_empleado}>
              <td>{e.nombre} {e.apellido}</td>
              <td>{e.nombre_usuario}</td>
              <td>{e.email}</td>
              <td>{e.rol}</td>
              <td>{e.activo ? 'Activo' : 'Inactivo'}</td>
              <td>
                <button
                  disabled={enProceso === e.id_empleado}
                  onClick={() => cambiarEstado(e, e.activo ? 'baja' : 'reactivar')}
                >
                  {e.activo ? 'Dar de baja' : 'Reactivar'}
                </button>{' '}
                <button onClick={() => abrirCambioContrasena(e)}>
                  Cambiar contraseña
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {aCambiar && (
        <form onSubmit={guardarContrasena} style={{ marginTop: 24 }}>
          <h3>Nueva contraseña para {aCambiar.nombre} {aCambiar.apellido}</h3>
          <input
            type="password"
            value={contrasenaNueva}
            onChange={(ev) => setContrasenaNueva(ev.target.value)}
            placeholder="Mínimo 8 caracteres"
            autoComplete="new-password"
          />{' '}
          <button type="submit" disabled={guardando}>Guardar</button>{' '}
          <button type="button" onClick={() => setACambiar(null)}>Cancelar</button>
          {errorContrasena && <p style={{ color: 'crimson' }}>{errorContrasena}</p>}
        </form>
      )}
    </div>
  );
}