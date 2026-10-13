import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axiosInstance from '../utils/api';
import { Header } from '../components/common/Header';
import { IncidentTimeline, IncidentRecord } from '../components/incidents/IncidentTimeline';
import { useAuth } from '../context/AuthContext';
import { History, RefreshCw } from 'lucide-react';

const fetchIncidents = async (): Promise<IncidentRecord[]> => {
  const { data } = await axiosInstance.get('/incidents');
  return Array.isArray(data) ? data : (data.incidents || []);
};

const IncidentTimelinePage: React.FC = () => {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();

  const { data: incidents = [], isLoading, error, refetch, isRefetching } = useQuery({
    queryKey: ['incidents'],
    queryFn: fetchIncidents,
    refetchInterval: 10000,
  });

  const acknowledgeMutation = useMutation({
    mutationFn: async (incidentId: string) => {
      await axiosInstance.post(`/incidents/${incidentId}/acknowledge`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incidents'] });
      queryClient.invalidateQueries({ queryKey: ['zones'] });
    },
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100">
      <Header />

      <main className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Header section */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-wide flex items-center gap-3">
              <History className="w-8 h-8 text-cyan-400" />
              Incident Timeline & Audit History
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Historical log of campus hazard triggers, risk escalations & operator acknowledgements
            </p>
          </div>

          <button
            onClick={() => refetch()}
            disabled={isRefetching}
            className="flex items-center space-x-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-semibold rounded-xl transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefetching ? 'animate-spin text-cyan-400' : ''}`} />
            <span>Refresh History</span>
          </button>
        </div>

        {/* Loading & Error States */}
        {isLoading ? (
          <div className="flex flex-col justify-center items-center py-20 text-slate-400">
            <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-cyan-500 mb-3"></div>
            <span>Loading incident history...</span>
          </div>
        ) : error ? (
          <div className="glass-panel p-6 text-center text-rose-400 border-rose-500/40">
            Failed to load incident history from the backend.
          </div>
        ) : (
          <IncidentTimeline
            incidents={incidents}
            canAcknowledge={isAuthenticated}
            onAcknowledge={(id) => acknowledgeMutation.mutate(id)}
          />
        )}
      </main>
    </div>
  );
};

export default IncidentTimelinePage;
