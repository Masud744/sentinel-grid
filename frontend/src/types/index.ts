export interface Zone {
  id: string;
  name: string;
  lab_type: string;
  is_active: boolean;
  connection_status: 'ONLINE' | 'OFFLINE';
  current_risk_score: number;
  current_state: 'SAFE' | 'WARNING' | 'CRITICAL';
  occupancy_status: 'OCCUPIED' | 'VACANT';
  is_trending_up?: boolean;
  trend_slope?: number;
  last_updated?: string;
}

export interface Incident {
  id: string;
  zone_id: string;
  zone_name: string;
  state: string;
  risk_score: number;
  cause: string;
  opened_at: string;
  resolved_at?: string;
  acknowledged?: boolean;
  acknowledged_by?: string;
}
