import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axiosInstance from '../utils/api';
import { useAuth } from '../context/AuthContext';
import { Shield, Lock, User, KeyRound, AlertCircle, ArrowRight } from 'lucide-react';

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const res = await axiosInstance.post('/auth/login', { username, password });
      const { access_token, refresh_token, user } = res.data;

      login(access_token, refresh_token, user);
      navigate(user.role === 'admin' ? '/admin' : '/');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Invalid username or password credentials.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const fillCredentials = (userType: 'admin' | 'staff') => {
    if (userType === 'admin') {
      setUsername('admin');
      setPassword('admin123');
    } else {
      setUsername('staff');
      setPassword('staff123');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white flex items-center justify-center p-4">
      <div className="glass-panel p-8 max-w-md w-full border-slate-800 shadow-2xl space-y-6 relative overflow-hidden">
        
        {/* Glow decoration */}
        <div className="absolute -top-20 -left-20 w-40 h-40 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none"></div>

        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-cyan-600 to-blue-600 flex items-center justify-center mx-auto shadow-lg shadow-cyan-500/20">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-extrabold tracking-wide">SCS-RG Portal</h2>
          <p className="text-xs text-slate-400">Smart Campus Safety & Response Grid Login</p>
        </div>

        {error && (
          <div className="p-3.5 rounded-xl bg-rose-950/80 border border-rose-500/40 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-300 font-semibold mb-1.5">Username</label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="text"
                required
                placeholder="Enter username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2.5 text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500 transition-colors"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1.5">Password</label>
            <div className="relative">
              <KeyRound className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="password"
                required
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2.5 text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500 transition-colors"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold rounded-xl shadow-lg shadow-cyan-900/30 transition-all flex items-center justify-center gap-2 text-sm mt-2"
          >
            <span>{isLoading ? 'Authenticating...' : 'Sign In to Grid'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        {/* Demo Quick Credentials */}
        <div className="pt-4 border-t border-slate-800/80 text-center space-y-2">
          <span className="text-[11px] text-slate-500 uppercase tracking-wider block font-semibold">Quick Demo Login</span>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <button
              type="button"
              onClick={() => fillCredentials('admin')}
              className="py-2 bg-slate-950/80 hover:bg-slate-900 border border-amber-500/30 text-amber-400 rounded-lg font-semibold transition-all"
            >
              Fill Admin
            </button>
            <button
              type="button"
              onClick={() => fillCredentials('staff')}
              className="py-2 bg-slate-950/80 hover:bg-slate-900 border border-cyan-500/30 text-cyan-400 rounded-lg font-semibold transition-all"
            >
              Fill Staff
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};

export default LoginPage;
