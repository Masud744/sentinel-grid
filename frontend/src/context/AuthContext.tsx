import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';

interface User {
  id: string;
  username: string;
  role: 'admin' | 'staff';
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string, refreshToken: string, user: User) => void;
  logout: () => void;
  isAuthenticated: boolean;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const savedUser = localStorage.getItem('scs_user');
    return savedUser ? JSON.parse(savedUser) : null;
  });
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('scs_token'));

  const login = (newToken: string, newRefreshToken: string, newUser: User) => {
    setToken(newToken);
    setUser(newUser);
    localStorage.setItem('scs_token', newToken);
    localStorage.setItem('scs_refresh_token', newRefreshToken);
    localStorage.setItem('scs_user', JSON.stringify(newUser));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('scs_token');
    localStorage.removeItem('scs_refresh_token');
    localStorage.removeItem('scs_user');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        logout,
        isAuthenticated: !!token,
        isAdmin: user?.role === 'admin',
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
