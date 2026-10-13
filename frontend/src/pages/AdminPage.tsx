import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axiosInstance from '../utils/api';
import { Header } from '../components/common/Header';
import { useAuth } from '../context/AuthContext';
import { ShieldAlert, Lock, AlertTriangle, CheckCircle2, History, Power, Send, ShieldCheck } from 'lucide-react';
import { Zone } from '../types';

interface AuditLog {
  id: string;
  actor: string;
  action: string;
  details: string;
  timestamp: string;
}

const fetchZones = async (): Promise<Zone[]> => {
  const { data } = await axiosInstance.get('/zones');
  return Array.isArray(data) ? data : (data.zones || []);
};

const fetchAuditLogs = async (): Promise<AuditLog[]> => {
  try {
    const { data } = await axiosInstance.get('/admin/audit-logs');
    return Array.isArray(data) ? data : (data.logs || []);
  } catch (e) {
    return [];
  }
};

const AdminPage: React.FC = () => {
  const { user, isAdmin } = useAuth();
  const queryClient = useQueryClient();

  const [selectedZoneId, setSelectedZoneId] = useState('');
  const [forcedState, setForcedState] = useState<'SAFE' | 'WARNING' | 'CRITICAL'>('SAFE');
  const [overrideReason, setOverrideReason] = useState('');
  const [feedbackMessage, setFeedbackMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const { data: zones = [] } = useQuery({
    queryKey: ['zones'],
    queryFn: fetchZones,
  });

  const { data: auditLogs = [] } = useQuery({
    queryKey: ['auditLogs'],
    queryFn: fetchAuditLogs,
    enabled: isAdmin,
  });

  const overrideMutation = useMutation({
    mutationFn: async () => {
      if (!selectedZoneId || !overrideReason) {
        throw new Error('Please select a zone and enter a valid override reason.');
      }
      await axiosInstance.post('/admin/override', {
        zone_id: selectedZoneId,
        forced_state: forcedState,
        reason: overrideReason,
      });
    },
    onSuccess: () => {
      setFeedbackMessage({ type: 'success', text: `Successfully applied state override (${forcedState})!` });
      setOverrideReason('');
      queryClient.invalidateQueries({ queryKey: ['zones'] });
      queryClient.invalidateQueries({ queryKey: ['auditLogs'] });
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || err.message || 'Failed to submit override.';
      setFeedbackMessage({ type: 'error', text: msg });
    },
  });

  const toggleZoneMutation = useMutation({
    mutationFn: async ({ zoneId, isActive }: { zoneId: string; isActive: boolean }) => {
      await axiosInstance.patch(`/admin/zones/${zoneId}`, { is_active: !isActive });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['zones'] });
      queryClient.invalidateQueries({ queryKey: ['auditLogs'] });
    },
  });

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100">
        <Header />
        <main className="p-6 max-w-2xl mx-auto py-24 text-center">
          <div className="glass-panel p-8 border-rose-500/40 space-y-4">
            <div className="w-16 h-16 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-400 flex items-center justify-center mx-auto">
              <Lock className="w-8 h-8" />
            </div>
            <h2 className="text-2xl font-bold text-white">RBAC Access Restricted</h2>
            <p className="text-sm text-slate-400">
              Only authorized Administrators have permission to access the Grid Manual Override & Admin Control Panel.
            </p>
            <p className="text-xs text-slate-500 font-mono">
              Current Role: <span className="text-amber-400 font-semibold">{user?.role || 'Unauthenticated'}</span>
            </p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100">
      <Header />

      <main className="p-6 max-w-7xl mx-auto space-y-8">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-wide flex items-center gap-3">
              <ShieldAlert className="w-8 h-8 text-amber-400" />
              Grid Admin Control & Manual Override
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Role-Based Access Control (RBAC) panel for emergency state overrides and audit monitoring
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Form: Manual Risk State Override */}
          <div className="glass-panel p-6 border-amber-500/30 space-y-6">
            <div className="flex items-center space-x-3 pb-3 border-b border-slate-800">
              <div className="p-2 rounded-xl bg-amber-500/20 text-amber-400">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-white text-base">Manual Zone State Override</h3>
                <p className="text-xs text-slate-400">Force a zone state in case of false alarm or emergency override</p>
              </div>
            </div>

            {feedbackMessage && (
              <div className={`p-4 rounded-xl text-xs font-semibold flex items-center gap-2 ${
                feedbackMessage.type === 'success' ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-500/40' : 'bg-rose-950/80 text-rose-300 border border-rose-500/40'
              }`}>
                {feedbackMessage.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
                <span>{feedbackMessage.text}</span>
              </div>
            )}

            <div className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-2">Select Target Zone</label>
                <select
                  value={selectedZoneId}
                  onChange={(e) => setSelectedZoneId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-white focus:outline-none focus:border-amber-500"
                >
                  <option value="">-- Choose Campus Zone --</option>
                  {zones.map((z) => (
                    <option key={z.id} value={z.id}>
                      {z.name} ({z.lab_type}) — Current: {z.current_state}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-2">Forced Override State</label>
                <div className="grid grid-cols-3 gap-3">
                  {(['SAFE', 'WARNING', 'CRITICAL'] as const).map((st) => (
                    <button
                      key={st}
                      type="button"
                      onClick={() => setForcedState(st)}
                      className={`py-2.5 rounded-lg font-bold border transition-all ${
                        forcedState === st
                          ? st === 'CRITICAL'
                            ? 'bg-rose-600 text-white border-rose-400'
                            : st === 'WARNING'
                            ? 'bg-amber-600 text-white border-amber-400'
                            : 'bg-emerald-600 text-white border-emerald-400'
                          : 'bg-slate-950/80 text-slate-400 border-slate-800 hover:text-white'
                      }`}
                    >
                      {st}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-2">Justification / Reason (Required for Audit Log)</label>
                <textarea
                  rows={3}
                  placeholder="e.g. Scheduled sensor maintenance / False alarm verification..."
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-white placeholder-slate-500 focus:outline-none focus:border-amber-500"
                />
              </div>

              <button
                type="button"
                onClick={() => overrideMutation.mutate()}
                disabled={overrideMutation.isPending}
                className="w-full py-3 bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold rounded-xl shadow-lg transition-all flex items-center justify-center gap-2"
              >
                <Send className="w-4 h-4" />
                <span>{overrideMutation.isPending ? 'Executing Override...' : 'Apply Manual Override'}</span>
              </button>
            </div>
          </div>

          {/* Zone Activation Management */}
          <div className="glass-panel p-6 space-y-6">
            <div className="flex items-center space-x-3 pb-3 border-b border-slate-800">
              <div className="p-2 rounded-xl bg-cyan-500/20 text-cyan-400">
                <Power className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-white text-base">Zone Grid Status Control</h3>
                <p className="text-xs text-slate-400">Enable or disable telemetry collection per zone</p>
              </div>
            </div>

            <div className="space-y-3">
              {zones.map((z) => (
                <div key={z.id} className="bg-slate-950/80 border border-slate-800 p-4 rounded-xl flex items-center justify-between">
                  <div>
                    <h4 className="font-bold text-white text-sm">{z.name}</h4>
                    <p className="text-xs text-slate-400">{z.lab_type} • ID: {z.id}</p>
                  </div>

                  <button
                    onClick={() => toggleZoneMutation.mutate({ zoneId: z.id, isActive: z.is_active })}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                      z.is_active
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 hover:bg-emerald-500/30'
                        : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                    }`}
                  >
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>{z.is_active ? 'Active' : 'Disabled'}</span>
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* System Audit Logs */}
        <div className="glass-panel p-6 space-y-4">
          <div className="flex items-center space-x-3 pb-3 border-b border-slate-800">
            <div className="p-2 rounded-xl bg-purple-500/20 text-purple-400">
              <History className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-white text-base">System Audit Logs</h3>
              <p className="text-xs text-slate-400">Tamper-evident record of all operator actions and manual overrides</p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/80 text-slate-400 uppercase font-mono border-b border-slate-800">
                <tr>
                  <th className="p-3">Timestamp</th>
                  <th className="p-3">Actor</th>
                  <th className="p-3">Action</th>
                  <th className="p-3">Details / Justification</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {auditLogs.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="p-6 text-center text-slate-500">
                      No audit logs recorded yet.
                    </td>
                  </tr>
                ) : (
                  auditLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-900/50">
                      <td className="p-3 text-slate-400">{new Date(log.timestamp).toLocaleString()}</td>
                      <td className="p-3 font-semibold text-cyan-400">{log.actor}</td>
                      <td className="p-3 font-bold text-white">{log.action}</td>
                      <td className="p-3 text-slate-300">{log.details}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

      </main>
    </div>
  );
};

export default AdminPage;
