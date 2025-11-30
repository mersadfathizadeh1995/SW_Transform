# Genetic Algorithm Inversion for Dispersion Curves

## Implementation Guide for Surface Wave Inversion

---

## 1. Introduction

Genetic Algorithm (GA) inversion is a global optimization technique well-suited for the non-linear, non-unique problem of inverting surface wave dispersion curves to obtain shear-wave velocity (Vs) profiles. GA mimics natural selection to evolve a population of candidate models toward the best-fit solution.

---

## 2. Problem Formulation

### 2.1 Forward Problem

Given a 1D velocity model **m** = [Vs₁, Vs₂, ..., Vsₙ, h₁, h₂, ..., hₙ₋₁]:
- Compute theoretical dispersion curve c_theory(f) using Thomson-Haskell method

### 2.2 Inverse Problem

Given observed dispersion curve c_obs(f):
- Find model **m** that minimizes misfit between c_theory and c_obs

### 2.3 Misfit Function

**Root Mean Square Error (RMSE):**
```
misfit = sqrt( (1/N) * Σ[(c_obs(fᵢ) - c_theory(fᵢ))²] )
```

**Weighted RMSE (accounting for uncertainties):**
```
misfit = sqrt( (1/N) * Σ[((c_obs(fᵢ) - c_theory(fᵢ)) / σᵢ)²] )
```

---

## 3. GA Algorithm

### 3.1 Chromosome Encoding

Each candidate model (individual) is encoded as a chromosome:

```
chromosome = [Vs_1, Vs_2, ..., Vs_n, h_1, h_2, ..., h_{n-1}]
```

**Example (4-layer model):**
```
[Vs_1, Vs_2, Vs_3, Vs_4, h_1, h_2, h_3]
# 4 Vs values + 3 thicknesses (half-space has infinite thickness)
```

### 3.2 Parameter Bounds

Define search space for each parameter:

```python
bounds = {
    'Vs': [(50, 400), (100, 600), (200, 800), (300, 1200)],  # m/s per layer
    'h': [(0.5, 10), (1, 20), (2, 50)]  # m per layer
}
```

### 3.3 GA Operations

#### A. Initialization
```python
def initialize_population(pop_size, bounds):
    population = []
    for _ in range(pop_size):
        individual = []
        for (lo, hi) in bounds:
            individual.append(np.random.uniform(lo, hi))
        population.append(individual)
    return population
```

#### B. Fitness Evaluation
```python
def evaluate_fitness(individual, obs_disp, freqs):
    model = decode_model(individual)
    theory_disp = forward_model(model, freqs)
    
    misfit = np.sqrt(np.mean((obs_disp - theory_disp)**2))
    fitness = 1.0 / (1.0 + misfit)  # Higher fitness = lower misfit
    
    return fitness
```

#### C. Selection (Tournament)
```python
def tournament_selection(population, fitnesses, tournament_size=3):
    selected = []
    for _ in range(len(population)):
        # Random tournament
        indices = np.random.choice(len(population), tournament_size, replace=False)
        best_idx = indices[np.argmax([fitnesses[i] for i in indices])]
        selected.append(population[best_idx].copy())
    return selected
```

#### D. Crossover (Blend)
```python
def blend_crossover(parent1, parent2, alpha=0.5):
    child1, child2 = [], []
    for p1, p2 in zip(parent1, parent2):
        d = abs(p1 - p2)
        lo = min(p1, p2) - alpha * d
        hi = max(p1, p2) + alpha * d
        child1.append(np.random.uniform(lo, hi))
        child2.append(np.random.uniform(lo, hi))
    return child1, child2
```

#### E. Mutation (Gaussian)
```python
def gaussian_mutation(individual, bounds, mutation_rate=0.1, sigma=0.1):
    mutated = individual.copy()
    for i in range(len(mutated)):
        if np.random.random() < mutation_rate:
            lo, hi = bounds[i]
            range_val = hi - lo
            mutated[i] += np.random.normal(0, sigma * range_val)
            mutated[i] = np.clip(mutated[i], lo, hi)
    return mutated
```

### 3.4 Main GA Loop

```python
def genetic_algorithm(obs_disp, freqs, bounds, 
                      pop_size=100, max_generations=500,
                      crossover_rate=0.8, mutation_rate=0.1,
                      elite_count=2, convergence_threshold=1e-4):
    """
    GA inversion for dispersion curve.
    
    Parameters
    ----------
    obs_disp : ndarray
        Observed phase velocities
    freqs : ndarray
        Frequencies of observations
    bounds : list of tuples
        [(lo, hi), ...] for each parameter
    
    Returns
    -------
    best_model : list
        Best-fit model parameters
    best_misfit : float
        Minimum misfit achieved
    history : list
        Misfit history for monitoring
    """
    
    # Initialize
    population = initialize_population(pop_size, bounds)
    history = []
    
    for gen in range(max_generations):
        # Evaluate fitness
        fitnesses = [evaluate_fitness(ind, obs_disp, freqs) for ind in population]
        
        # Track best
        best_idx = np.argmax(fitnesses)
        best_fitness = fitnesses[best_idx]
        best_misfit = 1.0 / best_fitness - 1.0
        history.append(best_misfit)
        
        # Check convergence
        if len(history) > 20:
            recent = history[-20:]
            if np.std(recent) < convergence_threshold:
                print(f"Converged at generation {gen}")
                break
        
        # Elitism: keep best individuals
        sorted_indices = np.argsort(fitnesses)[::-1]
        elites = [population[i].copy() for i in sorted_indices[:elite_count]]
        
        # Selection
        selected = tournament_selection(population, fitnesses)
        
        # Crossover
        offspring = []
        for i in range(0, len(selected) - 1, 2):
            if np.random.random() < crossover_rate:
                c1, c2 = blend_crossover(selected[i], selected[i+1])
            else:
                c1, c2 = selected[i].copy(), selected[i+1].copy()
            offspring.extend([c1, c2])
        
        # Mutation
        offspring = [gaussian_mutation(ind, bounds, mutation_rate) for ind in offspring]
        
        # Apply bounds constraints
        for ind in offspring:
            for i, (lo, hi) in enumerate(bounds):
                ind[i] = np.clip(ind[i], lo, hi)
        
        # New population = elites + offspring
        population = elites + offspring[:pop_size - elite_count]
    
    # Return best
    best_idx = np.argmax(fitnesses)
    return population[best_idx], best_misfit, history
```

---

## 4. Model Constraints

### 4.1 Monotonically Increasing Vs

Often Vs increases with depth. Enforce this:

```python
def enforce_increasing_vs(individual, n_layers):
    vs_part = individual[:n_layers]
    # Sort Vs in ascending order
    vs_sorted = sorted(vs_part)
    individual[:n_layers] = vs_sorted
    return individual
```

### 4.2 Fixed Poisson's Ratio

Typically assume Vp/Vs ratio:
```python
vp_vs_ratio = 1.73  # Poisson's ratio ≈ 0.25
Vp = Vs * vp_vs_ratio
```

### 4.3 Density Estimation (Gardner's relation)
```python
density = 310 * Vp**0.25  # kg/m³ (approximate)
```

---

## 5. Complete Implementation

```python
import numpy as np
from disba import PhaseDispersion

class GAInversion:
    """Genetic Algorithm inversion for dispersion curves."""
    
    def __init__(self, n_layers=4, vp_vs_ratio=1.73):
        self.n_layers = n_layers
        self.vp_vs_ratio = vp_vs_ratio
    
    def forward_model(self, Vs_list, h_list, frequencies):
        """Compute theoretical dispersion curve."""
        # Build full model
        thickness = list(h_list) + [0]  # Half-space
        Vs = list(Vs_list)
        Vp = [vs * self.vp_vs_ratio for vs in Vs]
        density = [1800 + 200 * i for i in range(len(Vs))]  # Simple gradient
        
        # Use disba
        pd = PhaseDispersion(*zip(thickness, Vp, Vs, density))
        periods = 1.0 / np.array(frequencies)
        
        try:
            cpr = pd(periods, mode=0, wave="rayleigh")
            return cpr.velocity
        except:
            return np.full(len(frequencies), np.nan)
    
    def decode_individual(self, individual):
        """Decode chromosome to model parameters."""
        n = self.n_layers
        Vs_list = individual[:n]
        h_list = individual[n:2*n-1]
        return Vs_list, h_list
    
    def misfit(self, individual, obs_vel, freqs):
        """Compute RMS misfit."""
        Vs_list, h_list = self.decode_individual(individual)
        theory_vel = self.forward_model(Vs_list, h_list, freqs)
        
        if np.any(np.isnan(theory_vel)):
            return 1e6  # Penalty for invalid models
        
        return np.sqrt(np.mean((obs_vel - theory_vel)**2))
    
    def invert(self, obs_vel, freqs, bounds_vs, bounds_h,
               pop_size=100, generations=500, verbose=True):
        """
        Run GA inversion.
        
        Parameters
        ----------
        obs_vel : ndarray
            Observed phase velocities
        freqs : ndarray
            Frequencies
        bounds_vs : list of tuples
            [(min, max), ...] for each layer Vs
        bounds_h : list of tuples
            [(min, max), ...] for each layer thickness
        
        Returns
        -------
        result : dict
            {'Vs': [...], 'h': [...], 'misfit': float, 'history': [...]}
        """
        
        # Flatten bounds
        bounds = list(bounds_vs) + list(bounds_h)
        n_params = len(bounds)
        
        # Initialize population
        population = []
        for _ in range(pop_size):
            ind = [np.random.uniform(lo, hi) for (lo, hi) in bounds]
            population.append(ind)
        
        # GA parameters
        elite_count = max(2, pop_size // 20)
        crossover_rate = 0.8
        mutation_rate = 0.15
        
        history = []
        best_ever = None
        best_misfit_ever = float('inf')
        
        for gen in range(generations):
            # Evaluate
            misfits = [self.misfit(ind, obs_vel, freqs) for ind in population]
            
            # Track best
            best_idx = np.argmin(misfits)
            best_misfit = misfits[best_idx]
            
            if best_misfit < best_misfit_ever:
                best_misfit_ever = best_misfit
                best_ever = population[best_idx].copy()
            
            history.append(best_misfit_ever)
            
            if verbose and gen % 50 == 0:
                print(f"Gen {gen}: best misfit = {best_misfit_ever:.2f} m/s")
            
            # Selection (tournament)
            selected = []
            for _ in range(pop_size):
                contestants = np.random.choice(pop_size, 3, replace=False)
                winner = contestants[np.argmin([misfits[c] for c in contestants])]
                selected.append(population[winner].copy())
            
            # Elitism
            sorted_idx = np.argsort(misfits)
            elites = [population[i].copy() for i in sorted_idx[:elite_count]]
            
            # Crossover (BLX-alpha)
            offspring = []
            for i in range(0, len(selected) - 1, 2):
                if np.random.random() < crossover_rate:
                    p1, p2 = selected[i], selected[i+1]
                    c1, c2 = [], []
                    for j in range(n_params):
                        lo = min(p1[j], p2[j])
                        hi = max(p1[j], p2[j])
                        d = hi - lo
                        c1.append(np.random.uniform(lo - 0.5*d, hi + 0.5*d))
                        c2.append(np.random.uniform(lo - 0.5*d, hi + 0.5*d))
                    offspring.extend([c1, c2])
                else:
                    offspring.extend([selected[i].copy(), selected[i+1].copy()])
            
            # Mutation
            for ind in offspring:
                for j in range(n_params):
                    if np.random.random() < mutation_rate:
                        lo, hi = bounds[j]
                        ind[j] += np.random.normal(0, 0.1 * (hi - lo))
            
            # Enforce bounds
            for ind in offspring:
                for j, (lo, hi) in enumerate(bounds):
                    ind[j] = np.clip(ind[j], lo, hi)
            
            # New population
            population = elites + offspring[:pop_size - elite_count]
        
        # Decode best
        Vs_list, h_list = self.decode_individual(best_ever)
        
        return {
            'Vs': list(Vs_list),
            'h': list(h_list),
            'misfit': best_misfit_ever,
            'history': history
        }


# Example usage
if __name__ == "__main__":
    # Synthetic observed dispersion curve
    freqs = np.linspace(5, 50, 30)
    
    # True model: 3 layers + half-space
    true_Vs = [150, 250, 400, 600]
    true_h = [3, 5, 10]
    
    # Generate "observed" data
    inv = GAInversion(n_layers=4)
    obs_vel = inv.forward_model(true_Vs, true_h, freqs)
    obs_vel += np.random.normal(0, 5, len(obs_vel))  # Add noise
    
    # Define search bounds
    bounds_vs = [(50, 300), (100, 500), (200, 700), (300, 1000)]
    bounds_h = [(1, 10), (2, 15), (5, 30)]
    
    # Run inversion
    result = inv.invert(obs_vel, freqs, bounds_vs, bounds_h,
                        pop_size=80, generations=300)
    
    print(f"\nInversion Result:")
    print(f"  Vs: {result['Vs']}")
    print(f"  h:  {result['h']}")
    print(f"  Misfit: {result['misfit']:.2f} m/s")
    print(f"\nTrue model:")
    print(f"  Vs: {true_Vs}")
    print(f"  h:  {true_h}")
```

---

## 6. Alternative: DEAP Framework

For more sophisticated GA operations, use DEAP:

```python
from deap import base, creator, tools, algorithms
import numpy as np

# Create types
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin)

toolbox = base.Toolbox()

# Attribute generators
def create_individual(bounds):
    return [np.random.uniform(lo, hi) for (lo, hi) in bounds]

toolbox.register("individual", tools.initIterate, creator.Individual,
                 lambda: create_individual(BOUNDS))
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

# Genetic operators
toolbox.register("mate", tools.cxBlend, alpha=0.5)
toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=0.1, indpb=0.2)
toolbox.register("select", tools.selTournament, tournsize=3)
toolbox.register("evaluate", evaluate_misfit)

# Run
pop = toolbox.population(n=100)
result, log = algorithms.eaSimple(pop, toolbox, cxpb=0.8, mutpb=0.2,
                                   ngen=300, verbose=True)
```

---

## 7. References

1. Dal Moro, G., et al. (2007). "Rayleigh wave dispersion curve inversion via genetic algorithms." *J. Applied Geophysics*, 61, 39-55.

2. Yamanaka, H., & Ishida, H. (1996). "Application of genetic algorithms to an inversion of surface-wave dispersion data." *Bull. Seism. Soc. Am.*, 86, 436-444.

3. Wadi Fatima Case Study (2018). SCIRP.

4. DEAP documentation: https://deap.readthedocs.io/
