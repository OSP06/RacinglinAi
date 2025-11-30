/**
 * F1 Team and Tyre Compound Colors
 */

export const TEAM_COLORS: Record<string, string> = {
  'Red Bull Racing': '#3671C6',
  'Mercedes': '#27F4D2',
  'Ferrari': '#E8002D',
  'McLaren': '#FF8000',
  'Aston Martin': '#229971',
  'Alpine': '#FF87BC',
  'Williams': '#64C4FF',
  'AlphaTauri': '#5E8FAA',
  'Alfa Romeo': '#C92D4B',
  'Haas F1 Team': '#B6BABD',
  'Kick Sauber': '#52E252',
  'RB': '#6692FF',
};

export const COMPOUND_COLORS: Record<string, string> = {
  'SOFT': '#DA291C',
  'MEDIUM': '#FFF200',
  'HARD': '#EBEBEB',
  'INTERMEDIATE': '#43B02A',
  'WET': '#00AEEF',
};

export const TRACK_STATUS_COLORS: Record<string, string> = {
  'GREEN': '#00FF00',
  'YELLOW': '#FFFF00',
  'SC': '#FFA500',
  'VSC': '#FF69B4',
  'RED': '#FF0000',
};

// Default color for unknown teams
export const DEFAULT_TEAM_COLOR = '#666666';

// Dark theme colors
export const THEME_COLORS = {
  background: '#0a0a0a',
  surface: '#1a1a1a',
  surfaceHover: '#2a2a2a',
  border: '#333333',
  text: '#ffffff',
  textSecondary: '#aaaaaa',
  textMuted: '#666666',
  primary: '#3671C6',
  success: '#00FF00',
  warning: '#FFA500',
  error: '#FF0000',
};

export function getTeamColor(team: string): string {
  return TEAM_COLORS[team] || DEFAULT_TEAM_COLOR;
}

export function getCompoundColor(compound: string): string {
  return COMPOUND_COLORS[compound] || '#666666';
}

export function getTrackStatusColor(status: string): string {
  return TRACK_STATUS_COLORS[status] || '#666666';
}
