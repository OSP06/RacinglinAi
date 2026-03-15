import { create } from 'zustand';

interface FilterState {
  season: number | null;
  grandPrix: string | null;
  selectedDrivers: string[];

  setSeason: (season: number | null) => void;
  setGrandPrix: (gp: string | null) => void;
  setSelectedDrivers: (drivers: string[]) => void;
  toggleDriver: (driver: string) => void;
  clearFilters: () => void;
}

export const useFilterStore = create<FilterState>((set) => ({
  // Default to 2024 so the dashboard isn't blank on first load, but
  // clearFilters resets to null so the user starts fresh.
  season: 2024,
  grandPrix: null,
  selectedDrivers: [],

  setSeason: (season) => set({ season, grandPrix: null, selectedDrivers: [] }),
  setGrandPrix: (grandPrix) => set({ grandPrix, selectedDrivers: [] }),
  setSelectedDrivers: (selectedDrivers) => set({ selectedDrivers }),

  toggleDriver: (driver) =>
    set((state) => ({
      selectedDrivers: state.selectedDrivers.includes(driver)
        ? state.selectedDrivers.filter((d) => d !== driver)
        : [...state.selectedDrivers, driver],
    })),

  // FIX: reset to null, not hardcoded 2024
  clearFilters: () => set({ season: null, grandPrix: null, selectedDrivers: [] }),
}));
