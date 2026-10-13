import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Shield, LayoutDashboard, History, ShieldAlert, LogOut, Radio, User } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useWebSocket } from '../../context/WebSocketContext';

export const Header: React.FC = () => {
  const { user, logout, isAdmin } = useAuth();
  const { isConnected } = useWebSocket();
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="sticky top-0 z-40 bg-slate-900/80 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-gradient-to-tr from-cyan-600 to-blue-600 rounded-xl shadow-lg shadow-cyan-500/20">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-white tracking-wide flex items-center gap-2">
              SCS-RG <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-medium">Grid Active</span>
            </h1>
            <p className="text-xs text-slate-400">Smart Campus Safety & Response Grid</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="hidden md:flex items-center space-x-1">
          <Link
            to="/"
            className={`px-3 py-2 rounded-lg text-sm font-medium flex items-center space-x-2 transition-all ${
              isActive('/')
                ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <LayoutDashboard className="w-4 h-4" />
            <span>Dashboard</span>
          </Link>

          <Link
            to="/incidents"
            className={`px-3 py-2 rounded-lg text-sm font-medium flex items-center space-x-2 transition-all ${
              isActive('/incidents')
                ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <History className="w-4 h-4" />
            <span>Incident Timeline</span>
          </Link>

          {isAdmin && (
            <Link
              to="/admin"
              className={`px-3 py-2 rounded-lg text-sm font-medium flex items-center space-x-2 transition-all ${
                isActive('/admin')
                  ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <ShieldAlert className="w-4 h-4" />
              <span>Admin Panel</span>
            </Link>
          )}
        </nav>

        {/* Status & User Profile */}
        <div className="flex items-center space-x-4">
          
          {/* WebSocket Status Indicator */}
          <div className="flex items-center space-x-2 bg-slate-950/60 border border-slate-800 px-3 py-1.5 rounded-full text-xs">
            <Radio className={`w-3.5 h-3.5 ${isConnected ? 'text-emerald-400 animate-pulse' : 'text-rose-500'}`} />
            <span className={isConnected ? 'text-slate-300' : 'text-rose-400'}>
              {isConnected ? 'LIVE FEED' : 'RECONNECTING'}
            </span>
          </div>

          {/* User Info & Logout */}
          <div className="flex items-center space-x-3 border-l border-slate-800 pl-4">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300">
                <User className="w-4 h-4" />
              </div>
              <div className="hidden sm:block text-left">
                <div className="text-xs font-semibold text-white">{user?.username}</div>
                <div className="text-[10px] text-cyan-400 uppercase font-medium">{user?.role}</div>
              </div>
            </div>

            <button
              onClick={logout}
              title="Logout"
              className="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>

        </div>
      </div>
    </header>
  );
};
