UNIFORM = False
PARETO = True

import random
import matplotlib.pyplot as plt
from scipy.optimize import fsolve

random.seed(2025)

round_number = 720
HB_user_number = 5
LR_user_number = 5

LR_min_demand = 100
LR_avg_demand = 300
LR_max_demand = 1000
HB_min_demand = 400
HB_avg_demand = 1000
HB_max_demand = 4000


class UniformGenerator:
    def __init__(self, min_value: float, max_value: float):
        self.min_value = min_value
        self.max_value = max_value

    def generate(self, len) -> float:
        return [random.uniform(self.min_value, self.max_value) for _ in range(len)]


class ParetoGenerator:
    """
    Generates numbers following the Pareto distribution with a specified minimum value,
    maximum value, and mean.
    """

    def __init__(self, min_value: float, max_value: float, mean: float):
        """
        Initializes the ParetoGenerator with the given parameters.

        Args:
            min_value (float): The minimum value of the distribution.
            max_value (float): The maximum value of the distribution.
            mean (float): The desired mean of the distribution.

        Raises:
            ValueError: If any of the input parameters are invalid
                        (e.g., min_value <= 0, max_value < min_value, mean < min_value).
        """
        if min_value <= 0:
            raise ValueError("min_value must be greater than 0")
        if max_value < min_value:
            raise ValueError("max_value must be greater than or equal to min_value")
        if mean < min_value:
            raise ValueError("mean must be greater than or equal to min_value")

        self.min_value = min_value
        self.max_value = max_value
        self.mean = mean
        self.alpha = (
            self._calculate_alpha()
        )  # Calculate alpha based on min, max, and mean

    def _calculate_alpha(self) -> float:
        """
        Calculates the alpha (shape) parameter of the Pareto distribution based on
        the desired min_value, max_value and mean.

        The formula to derive alpha is complex and requires numerical solution.
        We use scipy.optimize.fsolve to find the alpha.

        Returns:
            float: The calculated alpha parameter.
        """

        def pareto_mean(alpha, min_val, max_val, target_mean):
            if alpha <= 0:
                return float("inf")
            if alpha == 1:
                return float("inf")
            # The correct equation to solve for alpha, setting it equal to 0
            return (
                (alpha * min_val) / (alpha - 1)
                - (alpha * max_val ** (1 - alpha) * min_val**alpha)
                / (1 - (max_val / min_val) ** (-alpha))
                - target_mean
            )

        alpha_initial_guess = self.mean / (
            self.mean - self.min_value
        )  # Provide a reasonable starting point
        (alpha,) = fsolve(
            pareto_mean,
            alpha_initial_guess,
            args=(self.min_value, self.max_value, self.mean),
        )  # Unpack the result of fsolve

        return alpha

    def generate(self, size: int) -> list:
        """
        Generates a list of numbers following the Pareto distribution.

        Args:
            size (int): The number of values to generate.

        Returns:
            list: A list of numbers following the Pareto distribution with the
                  specified parameters.
        """

        samples = []
        for _ in range(size):
            # Generate from the standard Pareto
            standard_pareto = (random.random()) ** (-1 / self.alpha)
            # Scale and shift to fit the minimum value
            value = self.min_value * standard_pareto
            if value <= self.max_value:
                samples.append(value)
            else:
                samples.append(self.max_value)
        return samples
