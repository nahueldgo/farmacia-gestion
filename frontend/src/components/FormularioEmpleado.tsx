import { useState, type FormEvent } from 'react';
import { API_URL } from '../config/api';

interface Props {
  token: string | undefined;
  alCrear: (nombreCompleto: string) => void;
  alCancelar: () => void;
}

function datosVacios() {
  return {
    nombre: '',
    apellido: '',
    dni: '',
    rol: 'auxiliar',
    matricula: '',
    // en-CA da el formato AAAA-MM-DD con la fecha local, el que pide el backend
    fechaIngreso: new Date().toLocaleDateString('en-CA'),
    nombreUsuario: '',
    email: '',
    contrasena: '',
  };
}

export function FormularioEmpleado({ token, alCrear, alCancelar }: Props) {
  const [datos, setDatos] = useState(datosVacios());
  const [error, setError] = useState('');
  const [guardando, setGuardando] = useState(false);

  function actualizar(campo: keyof ReturnType<typeof datosVacios>, valor: string) {
    setDatos((anterior) => ({ ...anterior, [campo]: valor }));
  }

  async function enviar(evento: FormEvent) {
    evento.preventDefault();

    // Validaciones antes de molestar al backend
    if (
      !datos.nombre.trim() || !datos.apellido.trim() || !datos.dni.trim() ||
      !datos.nombreUsuario.trim() || !datos.email.trim() || !datos.fechaIngreso
    ) {
      setError('Completá todos los campos obligatorios.');
      return;
    }
    if (datos.rol === 'farmaceutico' && !datos.matricula.trim()) {
      setError('La matrícula es obligatoria para el farmacéutico.');
      return;
    }
    if (datos.contrasena.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres.');
      return;
    }

    setError('');
    setGuardando(true);
    try {
      const respuesta = await fetch(`${API_URL}/empleados`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          nombre: datos.nombre.trim(),
          apellido: datos.apellido.trim(),
          dni: datos.dni.trim(),
          rol: datos.rol,
          matricula_profesional: datos.matricula.trim() || null,
          fecha_ingreso: datos.fechaIngreso,
          nombre_usuario: datos.nombreUsuario.trim(),
          email: datos.email.trim(),
          contrasena: datos.contrasena,
        }),
      });

      if (!respuesta.ok) {
        const cuerpo = await respuesta.json().catch(() => null);
        setError(
          typeof cuerpo?.detail === 'string'
            ? cuerpo.detail
            : 'No se pudo crear el empleado. Revisá los datos.'
        );
        return;
      }
      alCrear(`${datos.nombre.trim()} ${datos.apellido.trim()}`);
    } catch {
      setError('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setGuardando(false);
    }
  }

  return (
    <form onSubmit={enviar} style={{ margin: '16px 0' }}>
      <h3>Nuevo empleado</h3>

      <label style={{ display: 'block', marginBottom: 8 }}>
        Nombre{' '}
        <input value={datos.nombre} onChange={(e) => actualizar('nombre', e.target.value)} />
      </label>
      <label style={{ display: 'block', marginBottom: 8 }}>
        Apellido{' '}
        <input value={datos.apellido} onChange={(e) => actualizar('apellido', e.target.value)} />
      </label>
      <label style={{ display: 'block', marginBottom: 8 }}>
        DNI{' '}
        <input value={datos.dni} onChange={(e) => actualizar('dni', e.target.value)} />
      </label>
      <label style={{ display: 'block', marginBottom: 8 }}>
        Rol{' '}
        <select value={datos.rol} onChange={(e) => actualizar('rol', e.target.value)}>
          <option value="auxiliar">Auxiliar</option>
          <option value="farmaceutico">Farmacéutico</option>
          <option value="dueno">Dueño</option>
        </select>
      </label>
      {datos.rol === 'farmaceutico' && (
        <label style={{ display: 'block', marginBottom: 8 }}>
          Matrícula profesional{' '}
          <input value={datos.matricula} onChange={(e) => actualizar('matricula', e.target.value)} />
        </label>
      )}
      <label style={{ display: 'block', marginBottom: 8 }}>
        Fecha de ingreso{' '}
        <input
          type="date"
          value={datos.fechaIngreso}
          onChange={(e) => actualizar('fechaIngreso', e.target.value)}
        />
      </label>
      <label style={{ display: 'block', marginBottom: 8 }}>
        Nombre de usuario{' '}
        <input
          value={datos.nombreUsuario}
          onChange={(e) => actualizar('nombreUsuario', e.target.value)}
        />
      </label>
      <label style={{ display: 'block', marginBottom: 8 }}>
        Email{' '}
        <input
          type="email"
          value={datos.email}
          onChange={(e) => actualizar('email', e.target.value)}
        />
      </label>
      <label style={{ display: 'block', marginBottom: 8 }}>
        Contraseña inicial{' '}
        <input
          type="password"
          value={datos.contrasena}
          onChange={(e) => actualizar('contrasena', e.target.value)}
          placeholder="Mínimo 8 caracteres"
          autoComplete="new-password"
        />
      </label>

      <button type="submit" disabled={guardando}>Crear empleado</button>{' '}
      <button type="button" onClick={alCancelar}>Cancelar</button>
      {error && <p style={{ color: 'crimson' }}>{error}</p>}
    </form>
  );
}