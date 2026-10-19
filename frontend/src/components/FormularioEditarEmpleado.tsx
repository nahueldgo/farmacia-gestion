import { useState, type FormEvent } from 'react';
import { API_URL } from '../config/api';

interface EmpleadoEditable {
  id_empleado: number;
  nombre: string;
  apellido: string;
  dni: string;
  rol: string;
  matricula_profesional: string | null;
  fecha_ingreso: string;
  nombre_usuario: string;
  email: string;
}

interface Props {
  token: string;
  empleado: EmpleadoEditable;
  alGuardar: (nombreCompleto: string) => void;
  alCancelar: () => void;
}

const ROLES = [
  { valor: 'dueno', etiqueta: 'Dueño' },
  { valor: 'farmaceutico', etiqueta: 'Farmacéutico' },
  { valor: 'auxiliar', etiqueta: 'Auxiliar' },
];

export function FormularioEditarEmpleado({ token, empleado, alGuardar, alCancelar }: Props) {
  const [nombre, setNombre] = useState(empleado.nombre);
  const [apellido, setApellido] = useState(empleado.apellido);
  const [rol, setRol] = useState(empleado.rol);
  const [matricula, setMatricula] = useState(empleado.matricula_profesional ?? '');
  const [fechaIngreso, setFechaIngreso] = useState(empleado.fecha_ingreso.slice(0, 10));
  const [email, setEmail] = useState(empleado.email);
  const [error, setError] = useState('');
  const [enviando, setEnviando] = useState(false);

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    setError('');

    if (!nombre.trim() || !apellido.trim() || !email.trim() || !fechaIngreso) {
      setError('Completá nombre, apellido, email y fecha de ingreso.');
      return;
    }
    if (!email.includes('@')) {
      setError('El email no es válido.');
      return;
    }
    if (rol === 'farmaceutico' && !matricula.trim()) {
      setError('La matrícula es obligatoria para el farmacéutico.');
      return;
    }

    // Mandamos solo los campos que cambiaron
    const cambios: Record<string, string | null> = {};
    if (nombre.trim() !== empleado.nombre) cambios.nombre = nombre.trim();
    if (apellido.trim() !== empleado.apellido) cambios.apellido = apellido.trim();
    if (rol !== empleado.rol) cambios.rol = rol;
    if (matricula.trim() !== (empleado.matricula_profesional ?? '')) {
      // Si la vacio, mandamos null para borrarla
      cambios.matricula_profesional = matricula.trim() || null;
    }
    if (fechaIngreso !== empleado.fecha_ingreso.slice(0, 10)) cambios.fecha_ingreso = fechaIngreso;
    if (email.trim() !== empleado.email) cambios.email = email.trim();

    if (Object.keys(cambios).length === 0) {
      setError('No hiciste ningún cambio.');
      return;
    }

    setEnviando(true);
    try {
      const respuesta = await fetch(`${API_URL}/empleados/${empleado.id_empleado}`, {
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
        setError('No tenés permiso para editar empleados.');
      } else if (!respuesta.ok) {
        let mensaje = 'No se pudieron guardar los cambios.';
        try {
          const datos = await respuesta.json();
          if (typeof datos.detail === 'string') mensaje = datos.detail;
        } catch {
          // si la respuesta no es JSON, dejamos el mensaje por defecto
        }
        setError(mensaje);
      } else {
        alGuardar(`${nombre.trim()} ${apellido.trim()}`);
      }
    } catch {
      setError('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form onSubmit={enviar} style={{ margin: '24px 0' }}>
      <h3>Editar a {empleado.nombre} {empleado.apellido}</h3>
      <p style={{ fontSize: 14, color: '#666' }}>
        DNI {empleado.dni} · Usuario {empleado.nombre_usuario} (no se pueden cambiar)
      </p>
      <div>
        <label>
          Nombre:{' '}
          <input value={nombre} onChange={(e) => setNombre(e.target.value)} />
        </label>
      </div>
      <div>
        <label>
          Apellido:{' '}
          <input value={apellido} onChange={(e) => setApellido(e.target.value)} />
        </label>
      </div>
      <div>
        <label>
          Rol:{' '}
          <select value={rol} onChange={(e) => setRol(e.target.value)}>
            {ROLES.map((r) => (
              <option key={r.valor} value={r.valor}>{r.etiqueta}</option>
            ))}
          </select>
        </label>
      </div>
      <div>
        <label>
          Matrícula {rol === 'farmaceutico' ? '(obligatoria)' : '(opcional)'}:{' '}
          <input value={matricula} onChange={(e) => setMatricula(e.target.value)} />
        </label>
      </div>
      <div>
        <label>
          Fecha de ingreso:{' '}
          <input
            type="date"
            value={fechaIngreso}
            onChange={(e) => setFechaIngreso(e.target.value)}
          />
        </label>
      </div>
      <div>
        <label>
          Email:{' '}
          <input value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
      </div>
      {error && <p style={{ color: 'crimson' }}>{error}</p>}
      <button type="submit" disabled={enviando}>
        {enviando ? 'Guardando...' : 'Guardar cambios'}
      </button>{' '}
      <button type="button" onClick={alCancelar}>Cancelar</button>
    </form>
  );
}