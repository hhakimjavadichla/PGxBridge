import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check for existing token on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('pgx_token');
    const storedUser = localStorage.getItem('pgx_user');
    
    if (storedToken && storedUser) {
      // Validate token with backend
      validateToken(storedToken).then(valid => {
        if (valid) {
          setToken(storedToken);
          setUser(JSON.parse(storedUser));
        } else {
          // Clear invalid token
          localStorage.removeItem('pgx_token');
          localStorage.removeItem('pgx_user');
        }
        setLoading(false);
      });
    } else {
      setLoading(false);
    }
  }, []);

  const validateToken = async (tokenToValidate) => {
    try {
      const response = await fetch('/api/auth/validate', {
        headers: {
          'Authorization': `Bearer ${tokenToValidate}`
        }
      });
      return response.ok;
    } catch {
      return false;
    }
  };

  const login = async (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch('/api/auth/login', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error?.message || 'Login failed');
    }

    const data = await response.json();
    
    // Store in state and localStorage
    setToken(data.token);
    setUser({
      username: data.username,
      role: data.role
    });
    
    localStorage.setItem('pgx_token', data.token);
    localStorage.setItem('pgx_user', JSON.stringify({
      username: data.username,
      role: data.role
    }));

    return data;
  };

  const logout = async () => {
    if (token) {
      try {
        const formData = new FormData();
        formData.append('authorization', `Bearer ${token}`);
        
        await fetch('/api/auth/logout', {
          method: 'POST',
          body: formData
        });
      } catch (err) {
        console.error('Logout error:', err);
      }
    }

    // Clear state and localStorage
    setToken(null);
    setUser(null);
    localStorage.removeItem('pgx_token');
    localStorage.removeItem('pgx_user');
  };

  const isAdmin = () => {
    return user?.role === 'admin';
  };

  const getAuthHeader = () => {
    if (token) {
      return { 'Authorization': `Bearer ${token}` };
    }
    return {};
  };

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    isAdmin,
    isAuthenticated: !!user,
    getAuthHeader
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
