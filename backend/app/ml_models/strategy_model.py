"""
Enhanced Strategy Prediction Model
Monte Carlo simulation for optimal pit strategy prediction
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass
class PitStop:
    """Pit stop details"""
    lap_number: int
    compound_from: str
    compound_to: str
    expected_loss_seconds: float
    confidence: float


@dataclass
class StrategyOption:
    """Strategy option with metrics"""
    strategy_name: str
    compounds: List[str]
    pit_stops: List[PitStop]
    expected_race_time: float
    win_probability: float
    percentile_10: float  # Best case
    percentile_90: float  # Worst case
    risk_score: float


class EnhancedStrategyPredictor:
    """
    Advanced strategy predictor using Monte Carlo simulation
    """

    def __init__(self):
        self.historical_data = None
        self.compound_performance = {}
        self.degradation_rates = {}
        self.pit_loss = 22.0  # Average pit loss in seconds
        self.safety_car_probability = 0.3  # 30% chance

    def analyze_historical_data(self, laps_df: pd.DataFrame):
        """
        Analyze historical data to learn patterns

        Args:
            laps_df: Historical lap data
        """
        logger.info("Analyzing historical pit stop data...")

        self.historical_data = laps_df

        # 1. Compound performance by stint length
        compound_stint_perf = {}

        for compound in ['SOFT', 'MEDIUM', 'HARD']:
            compound_laps = laps_df[laps_df['compound'] == compound]

            if len(compound_laps) > 0:
                # Average stint length
                avg_stint = compound_laps.groupby(['driver', 'stint'])['tyre_life'].max().mean()

                # Performance degradation rate
                if 'lap_time_seconds' in compound_laps.columns and 'tyre_life' in compound_laps.columns:
                    # Calculate degradation: lap time increase per lap
                    valid_laps = compound_laps[
                        (compound_laps['lap_time_seconds'] > 0) &
                        (compound_laps['tyre_life'] > 2) &
                        (compound_laps['is_valid_lap'] == True)
                    ]

                    if len(valid_laps) > 10:
                        # Group by tyre life and calculate mean lap time
                        deg_curve = valid_laps.groupby('tyre_life')['lap_time_seconds'].mean()

                        if len(deg_curve) > 5:
                            # Calculate degradation rate (slope)
                            from scipy.stats import linregress
                            slope, intercept, r_value, p_value, std_err = linregress(
                                deg_curve.index, deg_curve.values
                            )
                            degradation_rate = slope
                        else:
                            degradation_rate = 0.05  # Default
                    else:
                        degradation_rate = 0.05
                else:
                    degradation_rate = 0.05

                compound_stint_perf[compound] = {
                    'avg_stint_length': avg_stint,
                    'degradation_rate': degradation_rate,
                    'optimal_stint': int(avg_stint * 0.8)  # 80% of average for safety
                }

        # Default values for compounds without data
        defaults = {
            'SOFT': {'avg_stint_length': 15, 'degradation_rate': 0.08, 'optimal_stint': 12},
            'MEDIUM': {'avg_stint_length': 25, 'degradation_rate': 0.05, 'optimal_stint': 20},
            'HARD': {'avg_stint_length': 35, 'degradation_rate': 0.03, 'optimal_stint': 28}
        }

        for compound in ['SOFT', 'MEDIUM', 'HARD']:
            if compound not in compound_stint_perf:
                compound_stint_perf[compound] = defaults[compound]

        self.compound_performance = compound_stint_perf
        self.degradation_rates = {k: v['degradation_rate'] for k, v in compound_stint_perf.items()}

        logger.info(f"Compound performance analyzed: {self.compound_performance}")

        # 2. Safety car probability (from historical track data)
        if 'is_sc' in laps_df.columns:
            sc_laps = laps_df['is_sc'].sum()
            total_laps = len(laps_df)
            self.safety_car_probability = min(sc_laps / total_laps * 10, 0.5)  # Cap at 50%
        else:
            self.safety_car_probability = 0.3  # Default 30%

        logger.info(f"Safety car probability: {self.safety_car_probability:.2%}")

    def simulate_race(self, strategy: List[str], race_laps: int,
                      base_lap_time: float, randomize: bool = True) -> float:
        """
        Simulate a race with given strategy

        Args:
            strategy: List of compounds (e.g., ['SOFT', 'MEDIUM', 'MEDIUM'])
            race_laps: Total race laps
            base_lap_time: Base lap time for the car
            randomize: Add random variance

        Returns:
            Total race time in seconds
        """
        total_time = 0.0
        current_lap = 1

        # Fuel effect
        fuel_per_lap = 2.0  # kg
        fuel_effect_per_kg = 0.03  # seconds

        for stint_idx, compound in enumerate(strategy):
            # Determine stint length
            if stint_idx < len(strategy) - 1:
                # Not final stint - use optimal stint length
                stint_length = self.compound_performance[compound]['optimal_stint']
            else:
                # Final stint - use remaining laps
                stint_length = race_laps - current_lap + 1

            # Simulate each lap in stint
            for lap_in_stint in range(1, stint_length + 1):
                # Base lap time
                lap_time = base_lap_time

                # Fuel effect (gets faster as fuel burns)
                remaining_laps = race_laps - current_lap + 1
                fuel_weight = remaining_laps * fuel_per_lap
                fuel_penalty = fuel_weight * fuel_effect_per_kg
                lap_time += fuel_penalty

                # Tyre degradation
                deg_rate = self.degradation_rates[compound]

                # Warmup phase (first 2 laps slower)
                if lap_in_stint == 1:
                    lap_time += 1.5  # Out lap penalty
                elif lap_in_stint == 2:
                    lap_time += 0.3  # Warmup lap

                # Linear degradation
                lap_time += deg_rate * lap_in_stint

                # Cliff effect (last 20% of stint)
                cliff_lap = int(self.compound_performance[compound]['avg_stint_length'] * 0.8)
                if lap_in_stint > cliff_lap:
                    cliff_penalty = 0.1 * (lap_in_stint - cliff_lap) ** 1.5
                    lap_time += cliff_penalty

                # Random variance
                if randomize:
                    lap_time += np.random.normal(0, 0.2)  # ±0.2s standard deviation

                total_time += lap_time
                current_lap += 1

                if current_lap > race_laps:
                    break

            # Pit stop (except after last stint)
            if stint_idx < len(strategy) - 1:
                pit_loss = self.pit_loss + np.random.normal(0, 1.0) if randomize else self.pit_loss
                total_time += pit_loss

            if current_lap > race_laps:
                break

        return total_time

    def monte_carlo_strategy_evaluation(self, strategy: List[str], race_laps: int,
                                         base_lap_time: float, iterations: int = 1000) -> Dict:
        """
        Evaluate strategy using Monte Carlo simulation

        Args:
            strategy: Compound sequence
            race_laps: Total race laps
            base_lap_time: Base lap time
            iterations: Number of simulations

        Returns:
            Statistics dictionary
        """
        results = []

        for _ in range(iterations):
            # Simulate with randomness
            race_time = self.simulate_race(strategy, race_laps, base_lap_time, randomize=True)
            results.append(race_time)

        results = np.array(results)

        return {
            'mean': np.mean(results),
            'median': np.median(results),
            'std': np.std(results),
            'percentile_10': np.percentile(results, 10),  # Best case (optimistic)
            'percentile_90': np.percentile(results, 90),  # Worst case (pessimistic)
            'min': np.min(results),
            'max': np.max(results)
        }

    def predict_optimal_strategy(self, race_laps: int, base_lap_time: float,
                                  available_compounds: List[str] = None,
                                  current_lap: int = 1) -> List[StrategyOption]:
        """
        Predict optimal pit strategies

        Args:
            race_laps: Total race laps
            base_lap_time: Base lap time for the car
            available_compounds: Compounds available (default: all)
            current_lap: Current lap (for mid-race strategy)

        Returns:
            List of strategy options ranked by expected time
        """
        if available_compounds is None:
            available_compounds = ['SOFT', 'MEDIUM', 'HARD']

        logger.info(f"Predicting strategies for {race_laps} lap race (current lap: {current_lap})")

        # Generate strategy options
        strategies = []

        # 1-stop strategies
        for start_compound in available_compounds:
            for second_compound in available_compounds:
                strategies.append({
                    'name': f"1-stop: {start_compound[0]} → {second_compound[0]}",
                    'compounds': [start_compound, second_compound],
                    'stops': 1
                })

        # 2-stop strategies
        for c1 in available_compounds:
            for c2 in available_compounds:
                for c3 in available_compounds:
                    strategies.append({
                        'name': f"2-stop: {c1[0]} → {c2[0]} → {c3[0]}",
                        'compounds': [c1, c2, c3],
                        'stops': 2
                    })

        # Evaluate each strategy
        strategy_options = []

        for strat in strategies:
            # Monte Carlo evaluation
            mc_results = self.monte_carlo_strategy_evaluation(
                strat['compounds'],
                race_laps - current_lap + 1,
                base_lap_time,
                iterations=1000
            )

            # Calculate pit stop details
            pit_stops = []
            current_stint_lap = current_lap

            for i in range(len(strat['compounds']) - 1):
                compound_from = strat['compounds'][i]
                compound_to = strat['compounds'][i + 1]
                optimal_stint = self.compound_performance[compound_from]['optimal_stint']

                pit_lap = current_stint_lap + optimal_stint

                pit_stops.append(PitStop(
                    lap_number=pit_lap,
                    compound_from=compound_from,
                    compound_to=compound_to,
                    expected_loss_seconds=self.pit_loss,
                    confidence=0.85  # Default confidence
                ))

                current_stint_lap = pit_lap

            # Calculate risk score
            variance = mc_results['std']
            risk_score = min((variance / mc_results['mean']) * 100, 100)

            # Win probability (relative to best possible time)
            # Simplified: inverse of expected time
            win_prob = 0.0  # Will calculate after all strategies evaluated

            strategy_options.append(StrategyOption(
                strategy_name=strat['name'],
                compounds=strat['compounds'],
                pit_stops=pit_stops,
                expected_race_time=mc_results['mean'],
                win_probability=win_prob,
                percentile_10=mc_results['percentile_10'],
                percentile_90=mc_results['percentile_90'],
                risk_score=risk_score
            ))

        # Sort by expected time
        strategy_options.sort(key=lambda x: x.expected_race_time)

        # Calculate win probabilities
        best_time = strategy_options[0].expected_race_time
        worst_time = strategy_options[-1].expected_race_time

        for strat in strategy_options:
            # Inverse relationship: faster = higher probability
            if worst_time != best_time:
                strat.win_probability = 1 - ((strat.expected_race_time - best_time) / (worst_time - best_time))
                strat.win_probability = max(0.05, min(0.95, strat.win_probability))  # Clamp between 5-95%
            else:
                strat.win_probability = 0.5

        logger.info(f"Evaluated {len(strategy_options)} strategy options")
        logger.info(f"Best strategy: {strategy_options[0].strategy_name} ({strategy_options[0].expected_race_time:.1f}s)")

        # Return top 5 strategies
        return strategy_options[:5]

    def save_model(self, path: str):
        """Save model parameters"""
        import joblib
        joblib.dump({
            'compound_performance': self.compound_performance,
            'degradation_rates': self.degradation_rates,
            'pit_loss': self.pit_loss,
            'safety_car_probability': self.safety_car_probability
        }, path)
        logger.info(f"Strategy model saved to {path}")

    def load_model(self, path: str):
        """Load model parameters"""
        import joblib
        data = joblib.load(path)
        self.compound_performance = data['compound_performance']
        self.degradation_rates = data['degradation_rates']
        self.pit_loss = data['pit_loss']
        self.safety_car_probability = data['safety_car_probability']
        logger.info(f"Strategy model loaded from {path}")
