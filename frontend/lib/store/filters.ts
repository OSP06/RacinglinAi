import { create } from 'zustand';

interface FilterState {
  season: number | null;
  grandPrix: string | null;
  selectedDrivers: string[];

  // Actions
  setSeason: (season: number | null) => void;
  setGrandPrix: (gp: string | null) => void;
  setSelectedDrivers: (drivers: string[]) => void;
  toggleDriver: (driver: string) => void;
  clearFilters: () => void;
}

export const useFilterStore = create<FilterState>((set) => ({
  season: 2024, // Default to most recent season
  grandPrix: null,
  selectedDrivers: [],

  setSeason: (season) => set({ season, grandPrix: null }), // Reset GP when season changes
  setGrandPrix: (grandPrix) => set({ grandPrix }),
  setSelectedDrivers: (selectedDrivers) => set({ selectedDrivers }),

  toggleDriver: (driver) =>
    set((state) => ({
      selectedDrivers: state.selectedDrivers.includes(driver)
        ? state.selectedDrivers.filter((d) => d !== driver)
        : [...state.selectedDrivers, driver],
    })),

  clearFilters: () =>
    set({
      season: 2024,
      grandPrix: null,
      selectedDrivers: [],
    }),
}));
