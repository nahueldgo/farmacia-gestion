import { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';

export type Rol = 'auxiliar' | 'farmaceutico' | 'dueno';

interface Usuario {
  nombre: string;
  rol: Rol;
  token: string;
  debeCambiarContrasena: boolean;
}

interface AuthContextType {
  usuario: Usuario | null;
  login: (nombre: string, rol: Rol, token: string, debeCambiarContrasena: boolean) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null);

  const login = (nombre: string, rol: Rol, token: string, debeCambiarContrasena: boolean) => {
    setUsuario({ nombre, rol, token, debeCambiarContrasena });
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