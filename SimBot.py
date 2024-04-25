import os
import gym
import numpy as np
from gym import spaces
from matplotlib import pyplot as plt
from IPython.display import display


class Spell:
    def __init__(self, name, cooldown, damage):
        self.name = name
        self.cooldown = cooldown
        self.current_cooldown = 0
        self.damage = damage

    def cast(self, run_sim):
        if self.current_cooldown == 0:
            self.current_cooldown = self.cooldown
            # print(f"Casting {self.name}, setting cooldown to {self.cooldown}")
            return True
        # print(f"Cannot cast {self.name}, cooldown remaining: {self.current_cooldown}")
        return False

    def cooldown_tick(self):
        if self.current_cooldown > 0:
            self.current_cooldown -= 1


class Fireball(Spell):

    def cast(self, run_sim):
        if super().cast(run_sim):
            training_dummy = run_sim.training_dummy
            training_dummy.calc_damage(self.damage)
            return True
        return False


class Frostbolt(Spell):
    def cast(self, run_sim):
        if super().cast(run_sim):
            training_dummy = run_sim.training_dummy
            training_dummy.calc_damage(self.damage)
            return True
        return False


class BloodMoonCrescent(Spell):

    def cast(self, run_sim):
        if super().cast(run_sim):
            training_dummy = run_sim.training_dummy
            training_dummy.calc_damage(self.damage)
            return True
        return False


class Blaze(Spell):
    def cast(self, run_sim):
        if super().cast(run_sim):
            character = run_sim.character
            training_dummy = run_sim.training_dummy
            if character.last_spell == "Fireball":
                applied_damage = self.damage * 5
                training_dummy.calc_damage(applied_damage)
                # print(f"Blaze cast after Fireball, damage applied: {applied_damage}")
            else:
                training_dummy.calc_damage(self.damage)
                # print(f"Blaze cast without Fireball, damage applied: {self.damage}")
            return True
        return False


class ScorchDot(Spell):
    def __init__(self, name, cooldown, duration, damage):
        super().__init__(name, cooldown, damage)
        self.duration = duration

    def cast(self, run_sim):
        if super().cast(run_sim):
            training_dummy = run_sim.training_dummy
            training_dummy.apply_dot(self.damage, self.duration)
            return True
        return False


class Combustion(Spell):
    def __init__(self, name, cooldown, duration, damage_increase):
        super().__init__(name, cooldown, duration)
        self.duration = duration
        self.damage_increase = damage_increase

    def cast(self, run_sim):
        if super().cast(run_sim):
            # training_dummy = run_sim.training_dummy
            character = run_sim.character
            character.activate_buff(self.name, self.duration, self.damage_increase)
            return True
        return False


class TrainingDummy:

    def __init__(self, character):
        self.dot_damage = 0
        self.dot_timer = 0
        self.damage_taken = 0
        self.character = character

    def apply_dot(self, dot_damage, duration):
        self.dot_timer = duration
        self.dot_damage = dot_damage

    def tick(self):
        # Check Dot-Timer
        if self.dot_timer > 0:
            self.dot_timer -= 1
            self.calc_damage(self.dot_damage)

    def calc_damage(self, damage):
        if self.character.buff_active:
            self.damage_taken += damage * (1+self.character.buff_damage_increase)
        else:
            self.damage_taken += damage


class Character:
    def __init__(self):
        self.buff_damage_increase = 0.0
        self.buff_name = ""
        self.buff_active = False
        self.buff_timer = 0
        self.last_spell = None

    def activate_buff(self, name, duration, damage_increase):
        self.buff_active = True
        self.buff_timer = duration
        self.buff_name = name
        self.buff_damage_increase = damage_increase

    # Check Buff-Timer
    def tick(self):
        if self.buff_timer > 0:
            self.buff_timer -= 1
            if self.buff_timer == 0:
                self.buff_active = False


class RunSim:
    training_dummy = None

    def __init__(self):
        self.character = Character()
        self.training_dummy = TrainingDummy(self.character)    # Because the trainingsdummy must know,
        # List of spells                                            # the buff of the player
        self.spells = {

            'Fireball': Fireball('Fireball', 0, 10),                                # Name, Cooldown, Damage
            'Frostbolt': Frostbolt('Frostbolt', 0, 3),                              # Name, Cooldown, Damage
            'BloodMoonCrescent': BloodMoonCrescent('BloodMoonCrescent', 10, 80),    # Name, Cooldown, Damage
            'Blaze': Blaze('Blaze', 0, 5),                                          # Name, Cooldown, Damage
            'ScorchDot': ScorchDot('ScorchDot', 0, 20, 5),                          # Name, Cooldown, Duration, Damage
            'Combustion': Combustion('Combustion', 60, 25, 0.5)                     # Name, Cooldown, Duration, Damage_increase
        }
        self.spell_cast_count = {name: 0 for name in self.spells.keys()}

    # Reset-function for Reinforcement Learning
    def reset(self):
        self.character = Character()
        self.training_dummy = TrainingDummy(self.character)
        for spell in self.spells.values():
            spell.current_cooldown = 0
        self.spell_cast_count = {name: 0 for name in self.spells.keys()}
        return self.get_results()

    def step(self, action_name):
        # Check last_casted_spell & increase cast_count
        spell = self.spells[action_name]
        if spell.cast(self):
            self.character.last_spell = spell.name
            self.spell_cast_count[action_name] += 1

        # Check Dot-Spell/Buff Tick
        self.training_dummy.tick()
        self.character.tick()

        # Check Cooldown Tick
        for spell in self.spells.values():
            spell.cooldown_tick()

        # Create output for visualisation
        self.render()

    def render(self):
        """
        print(f"Total Damage: {self.training_dummy.damage_taken} damage")
        print(f"- - - - - - - - - - - - - - - - - - - - - - - - - -")
        print(f"Remaining DoT Duration: {self.training_dummy.dot_timer}")
        print(f"Remaining Buff Duration: {self.character.buff_timer}. "
              f" CD-Buff: {self.spells['Combustion'].current_cooldown}."
              f" CD-Moon: {self.spells['BloodMoonCrescent'].current_cooldown}")
        print(f"- - - - - - - - - - - - - - - - - - - - - - - - - -")
        print(f"Spell cast last time: {self.character.last_spell}")
        print(f"- - - - - - - - - - - - - - - - - - - - - - - - - -")
        print(f"- - - - - - - - - - - - - - - - - - - - - - - - - -")
        print(f"- - - - - - - - - - - - - - - - - - - - - - - - - -")
        """

    def get_results(self):
        cooldowns = [spell.current_cooldown / 60 for _, spell in self.spells.items()]
        cast_counts = [self.spell_cast_count[name] / global_max_ticks for name in self.spells.keys()]
        last_spell = [1] if self.character.last_spell == 'Blaze' else [0]
        state = [self.training_dummy.damage_taken] + cooldowns + cast_counts + last_spell
        return np.array(state, dtype=np.float32)


def run_simulation():
    class RunSimEnv(gym.Env):
        def __init__(self):
            super(RunSimEnv, self).__init__()
            self.tick_count = 0
            self.env = RunSim()
            # Action space: one discrete action per spell
            self.action_space = spaces.Discrete(len(self.env.spells))
            # Observation space: assuming some max values for illustration
            max_cooldown = 60
            max_damage = global_max_damage
            max_count = global_max_ticks
            last_spell = 0
            num_features = 1 + 2 * len(self.env.spells) + 1  # total_damage + cd*6 (foreach spell) + last_spell
            self.observation_space = spaces.Box(
                low=np.zeros(num_features, dtype=np.float32),  # All lows are 0
                high=np.array([max_damage] + ([max_count]+[max_cooldown])*len(self.env.spells) + [last_spell]),
                # low=np.float32(0),
                # high=np.float32(np.inf),
                # shape=(num_features,),
                dtype=np.float32
            )

        def step(self, action):
            # action is a np.int64

            action_name = list(self.env.spells.keys())[action]
            self.env.step(action_name)
            obs = self.env.get_results()
            reward = obs[0]  # Total-damage in numpy get_results()
            done = self.tick_count >= global_max_ticks
            self.tick_count += 1  # Increment tick count for Done
            return obs, reward, done, {}

        def reset(self, **kwargs):
            self.tick_count = 0  # Reset tick count
            return self.env.reset()

        def render(self, mode='human'):
            self.env.render()

    def initialize_population(pop_size, action_space, sequence_length):
        return [np.random.randint(action_space.n, size=sequence_length)
                for _ in range(pop_size)]

    def evaluate_population(ep_env, population):
        fitness_scores = []
        for solution in population:
            fitness = evaluate_solution(ep_env, solution)[0]
            fitness_scores.append((solution, fitness))
        return fitness_scores

    def evaluate_solution(es_env, solution):
        obs = es_env.reset()
        total_reward = 0
        best_reward = 0
        for action in solution:
            obs, reward, done, info = es_env.step(action)
            total_reward += reward
            if reward > best_reward:
                best_reward = reward
            if done:
                break
        return [total_reward, best_reward]

    def crossover(parent1, parent2):
        # Single-point crossover
        crossover_point = np.random.randint(1, len(parent1))
        child1 = np.concatenate([parent1[:crossover_point], parent2[crossover_point:]])
        child2 = np.concatenate([parent2[:crossover_point], parent1[crossover_point:]])
        return child1, child2

    def tournament_selection(ts_env, population, k=3):
        idxes = [np.random.randint(len(population)) for _ in range(k)]
        selected = [population[idx] for idx in idxes]
        selected_fitness = [evaluate_solution(ts_env, sol) for sol in selected]

        # Find the index of the solution with the highest total_reward manually
        max_fitness = -float('inf')  # Assumes fitness can't be lower than this
        best_index = 0
        for i, fitness in enumerate(selected_fitness):
            if fitness[0] > max_fitness:  # Assuming the first element is total_reward
                max_fitness = fitness[0]
                best_index = i

        return selected[best_index]

    def mutate(solution, mutation_rate, action_space):
        for i in range(len(solution)):
            if np.random.rand() < mutation_rate:
                solution[i] = np.random.randint(action_space.n)
        return solution

    def adapt_mutation_rate(current_rate, generations_without_improvement, max_rate=0.05, min_rate=0.01):
        if generations_without_improvement > 10:  # No improvement for 10 generations
            new_rate = min(current_rate * 1.3, max_rate)
            print("No improvement since", generations_without_improvement, "mutation_rate is getting raised to", new_rate)
        else:
            new_rate = max(current_rate * 0.95, min_rate)
            print("Improvement since", generations_without_improvement, "mutation_rate is getting lowered to", new_rate)
        return new_rate

    def draw_plot_all_gen(line, ax, fig, list_best_damage, list_generation):

        ax.set_xlabel('Generation')
        ax.set_ylabel('Total Damage')
        ax.set_xlim(0, global_generations)  # Use the number of generations for the x-axis limit
        ax.set_ylim(0, global_max_damage*1.1)  # Example: set maximum possible damage

        line.set_data(list_generation, list_best_damage)

        fig.canvas.draw()
        fig.canvas.flush_events()

        # Animated Version
        """
        line.set_data(list_generation, list_best_damage)
        ax.relim()
        ax.autoscale_view()

        ax.figure.canvas.draw()
        ax.figure.canvas.flush_events()
        """
    list_all_solutions = []

    def genetic_algorithm(ga_env, pop_size, generations, sequence_length, mutation_rate):
        # Initialize population
        population = initialize_population(pop_size, ga_env.action_space, sequence_length)
        os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'  # This is specific to certain OS environments
        plt.ion()
        fig = plt.figure()
        ax = fig.add_subplot(111)

        list_best_damages = []
        list_generations = []

        generations_without_improvement = 0
        saved_damage_peak = 0.0

        ax.axhline(y=global_current_record, color='g', linestyle='--', linewidth=1, label='Current record')
        ax.axhline(y=global_max_damage, color='r', linestyle='-', linewidth=1, label='Max Damage')

        line1, = ax.plot(list_generations, list_best_damages, linestyle='-', color='b')

        for generation in range(generations):

            # Evaluate all solutions in the population
            best_damage = max([evaluate_solution(ga_env, sol)[1] for sol in population])

            # Alter mutation_rate
            if saved_damage_peak == 0:
                saved_damage_peak = best_damage
            if best_damage == saved_damage_peak:
                generations_without_improvement += 1
            else:
                generations_without_improvement = 0
                saved_damage_peak = best_damage

            # Adapt mutation_rate if there are too many generations without improvement
            mutation_rate = adapt_mutation_rate(mutation_rate, generations_without_improvement, global_max_mutation_rate, global_min_mutation_rate)

            # Print the damage that the generation did
            print(f"Generation {generation}: Max Damage {best_damage} of {global_max_damage}, that's {best_damage/global_max_damage*100:.2f}%")

            # Set up plot for live updating
            list_best_damages.append(best_damage)
            list_generations.append(generation)

            # Draw live-plot
            draw_plot_all_gen(line1, ax, fig, list_best_damages, list_generations)
            plt.pause(0.01)

            # Save generation in list
            list_all_solutions.append(max(evaluate_population(ga_env, population), key=lambda x: x[1]))

            # Create the next generation
            new_population = []
            while len(new_population) < pop_size:
                # Random of top 10%
                # index1, index2 = np.random.choice(len(top_indices), 2, replace=False)
                # parent1, parent2 = population[index1], population[index2]

                # Tournament Selection
                parent1 = tournament_selection(ga_env, population, global_tournament_k_amount)
                parent2 = tournament_selection(ga_env, population, global_tournament_k_amount)

                child1, child2 = crossover(parent1, parent2)
                child1 = mutate(child1, mutation_rate, ga_env.action_space)
                child2 = mutate(child2, mutation_rate, ga_env.action_space)

                new_population.extend([child1, child2])

            population = new_population

        plt.ioff()
        plt.show()
        return population

    env = RunSimEnv()

    pop_size = global_pop_size
    generations = global_generations
    sequence_length = global_max_ticks

    best_population = genetic_algorithm(env, pop_size, generations, sequence_length, start_population_mutation_rate)
    fitness_scores = evaluate_population(env, best_population)
    best_solution, best_fitness = max(fitness_scores, key=lambda x: x[1])

    print("Best Performing Solution:")
    print("Sequence of recent actions (spells):", best_solution)
    print("Sequence of best actions (spells):", max(list_all_solutions, key=lambda x: x[1]))
    # print(list_all_solutions)


# const stats
global_max_damage = 4242.5
global_current_record = 4112.5
global_max_ticks = 128

# duration
global_generations = 100

# parameter for cross-entropy
global_pop_size = 30  # 50
global_population_top_n_index = 0.1
start_population_mutation_rate = 0.01  # 0.01
global_tournament_k_amount = 3  # 10% of pop_size probably
global_max_mutation_rate = 0.015  # 0.015
global_min_mutation_rate = 0.005  # 0.005

# TODO: Cross-over-rate?
# TODO: Reward Function that punishes similarity
# TODO: Diversity Checks
# TODO: New Spell: Fireball gives a stack of "flaming", each stack increases the damage of the new spell by 15%, stackable for 20 Stacks


if __name__ == "__main__":
    run_simulation()


# TODO: Parameteroptimierung, da Overfittung bei 95%
# TODO: Plotten von Generationen in Farben

# TODO: Parameter durch Cross-Entropy versuchen
# TODO: Datenbank auslagern?

"""
6 Stages of Success:
    1. Done!        Stop casting spells, that are on cooldown
    2. Done!        Stop casting Frostbolt, because its useless
    3. Done!        Stop casting DoT, when its already active
    4. Done!        Casting Combustion and BloodMoon on Cooldown, because it does most damage
    5. Done!        Alternating between Fireball and Blaze
    6. Oftentimes!  Waiting for BloodMoon cooldown when buff-cd is going to expire soon
"""
