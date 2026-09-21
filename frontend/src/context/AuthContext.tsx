import { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';

type Rol = 'auxiliar' | 'farmaceutico' | 'dueño';

interface Usuario {
  nombre: string;
  rol: Rol;
}

interface AuthContextType {
  usuario: Usuario | null;
  login: (nombre: string, rol: Rol) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null);

  const login = (nombre: string, rol: Rol) => {
    setUsuario({ nombre, rol });
  };

  const logout = () => {
    setUsuario(null);
  };

  return (
    <AuthContext.Provider value={{ usuario, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth debe usarse dentro de AuthProvider');
  return context;
}