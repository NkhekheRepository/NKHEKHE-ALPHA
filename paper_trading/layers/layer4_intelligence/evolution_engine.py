"""
Layer 4: Evolution Engine
==========================
Genetic algorithm for strategy evolution.
Runs multiple system variants and allocates capital to best performers.
"""

from typing import Dict, Any, Optional, List, Tuple
import numpy as np
from dataclasses import dataclass, field
from copy import deepcopy
from loguru import logger


@dataclass
class Genome:
    """Strategy parameter genome"""
    strategy_id: str
    params: Dict[str, float]
    fitness: float = 0.0
    age: int = 0
    trades: int = 0
    returns: List[float] = field(default_factory=list)

    @property
    def sharpe(self) -> float:
        if len(self.returns) < 5:
            return 0.0
        return float(np.mean(self.returns) / (np.std(self.returns) + 1e-8))

    def to_dict(self) -> Dict[str, Any]:
        return {
            'strategy_id': self.strategy_id,
            'params': self.params,
            'fitness': self.fitness,
            'age': self.age,
            'trades': self.trades,
            'sharpe': self.sharpe
        }


class EvolutionEngine:
    """
    Genetic algorithm for evolving strategy parameters.
    - Crossover and mutation of strategy genomes
    - Tournament selection of best performers
    - Dynamic capital allocation based on fitness
    """

    def __init__(self, config: Dict[str, Any] = None):
        config = config or {}
        self.population_size = config.get('population_size', 20)
        self.mutation_rate = config.get('mutation_rate', 0.15)
        self.crossover_rate = config.get('crossover_rate', 0.7)
        self.tournament_size = config.get('tournament_size', 3)
        self.elite_count = config.get('elite_count', 2)
        self.mutation_scale = config.get('mutation_scale', 0.2)

        self.population: List[Genome] = []
        self.generation = 0
        self._init_population(config.get('base_params', {}))

        logger.info(f"EvolutionEngine initialized (pop={self.population_size})")

    def _init_population(self, base_params: Dict[str, float]):
        """Initialize population with random variants of base params"""
        default_params = {
            'stop_loss': 2.0,
            'take_profit': 5.0,
            'atr_period': 14,
            'adx_threshold': 25.0,
            'rsi_period': 14,
            'momentum_weight': 0.5,
            'mean_reversion_weight': 0.3,
            'breakout_weight': 0.2,
            'position_size_pct': 10.0
        }
        default_params.update(base_params)

        for i in range(self.population_size):
            params = {}
            for key, value in default_params.items():
                noise = np.random.normal(0, self.mutation_scale * abs(value))
                params[key] = max(0.01, value + noise)

            self.population.append(Genome(
                strategy_id=f"gen0_variant_{i}",
                params=params
            ))

    def evolve(self) -> List[Genome]:
        """Run one generation of evolution"""
        self.generation += 1

        if len(self.population) < 2:
            return self.population

        self._evaluate_fitness()

        new_population = []

        sorted_pop = sorted(self.population, key=lambda g: g.fitness, reverse=True)
        for genome in sorted_pop[:self.elite_count]:
            genome.age += 1
            new_population.append(genome)

        while len(new_population) < self.population_size:
            parent1 = self._tournament_select()
            parent2 = self._tournament_select()

            if np.random.random() < self.crossover_rate:
                child1, child2 = self._crossover(parent1, parent2)
            else:
                child1, child2 = deepcopy(parent1), deepcopy(parent2)

            child1 = self._mutate(child1)
            child2 = self._mutate(child2)

            child1.strategy_id = f"gen{self.generation}_{len(new_population)}"
            child2.strategy_id = f"gen{self.generation}_{len(new_population) + 1}"

            child1.age = 0
            child2.age = 0

            new_population.extend([child1, child2])

        self.population = new_population[:self.population_size]

        best = sorted_pop[0]
        logger.info(f"Generation {self.generation} - Best fitness: {best.fitness:.4f}, Sharpe: {best.sharpe:.4f}")

        return self.population

    def _evaluate_fitness(self):
        """Calculate fitness for each genome"""
        for genome in self.population:
            if genome.trades < 5:
                genome.fitness = 0.0
                continue

            mean_ret = np.mean(genome.returns) if genome.returns else 0.0
            std_ret = np.std(genome.returns) if genome.returns else 1.0
            sharpe = mean_ret / (std_ret + 1e-8)

            downside = [r for r in genome.returns if r < 0]
            sortino = mean_ret / (np.std(downside) + 1e-8) if downside else sharpe

            age_bonus = min(0.1, genome.age * 0.01)

            genome.fitness = 0.5 * sharpe + 0.3 * sortino + 0.1 * age_bonus + 0.1 * mean_ret

    def _tournament_select(self) -> Genome:
        """Tournament selection"""
        candidates = np.random.choice(self.population, size=self.tournament_size, replace=False)
        return max(candidates, key=lambda g: g.fitness)

    def _crossover(self, parent1: Genome, parent2: Genome) -> Tuple[Genome, Genome]:
        """Uniform crossover"""
        child1_params = {}
        child2_params = {}

        for key in parent1.params:
            if np.random.random() < 0.5:
                child1_params[key] = parent1.params[key]
                child2_params[key] = parent2.params[key]
            else:
                child1_params[key] = parent2.params[key]
                child2_params[key] = parent1.params[key]

        return (
            Genome(strategy_id="", params=child1_params),
            Genome(strategy_id="", params=child2_params)
        )

    def _mutate(self, genome: Genome) -> Genome:
        """Gaussian mutation"""
        for key in genome.params:
            if np.random.random() < self.mutation_rate:
                value = genome.params[key]
                noise = np.random.normal(0, self.mutation_scale * abs(value))
                genome.params[key] = max(0.01, value + noise)
        return genome

    def record_result(self, strategy_id: str, return_pct: float):
        """Record trade result for a strategy"""
        for genome in self.population:
            if genome.strategy_id == strategy_id:
                genome.returns.append(return_pct)
                genome.trades += 1
                if len(genome.returns) > 500:
                    genome.returns = genome.returns[-500:]
                break

    def get_best_genomes(self, n: int = 5) -> List[Dict[str, Any]]:
        """Get top N performing genomes"""
        sorted_pop = sorted(self.population, key=lambda g: g.fitness, reverse=True)
        return [g.to_dict() for g in sorted_pop[:n]]

    def get_capital_allocation(self, total_capital: float) -> Dict[str, float]:
        """Allocate capital based on fitness scores"""
        self._evaluate_fitness()

        total_fitness = sum(max(0, g.fitness) for g in self.population)
        if total_fitness == 0:
            return {g.strategy_id: total_capital / len(self.population) for g in self.population}

        allocations = {}
        for genome in self.population:
            weight = max(0, genome.fitness) / total_fitness
            allocations[genome.strategy_id] = weight * total_capital

        return allocations

    def get_status(self) -> Dict[str, Any]:
        best = max(self.population, key=lambda g: g.fitness) if self.population else None
        return {
            'generation': self.generation,
            'population_size': len(self.population),
            'best_fitness': best.fitness if best else 0.0,
            'best_sharpe': best.sharpe if best else 0.0,
            'best_strategy_id': best.strategy_id if best else 'none'
        }
