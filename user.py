import math, random
from scipy import integrate
from scipy.optimize import minimize_scalar

from demand import ParetoGenerator

random.seed(2025)


# Target area is 10x10 meters
X_area, Y_area = 100.0, 100.0
# Broker's position is at the center of the area
X_broker, Y_broker = X_area / 2.0, Y_area / 2.0
# Transmission power in watts
transmission_power = 0.1
# Noise figure in watts (-96 dBm)
noise = 2.51e-13
# Bandwidth in Hz
bandwidth = 360_000
# Carrier frequency in Hz (default is 2.4e9 Hz for 2.4 GHz)
frequency = 2.4e9
# Speed of light in m/s
c = 3e8
# Height of the broker in meters
H = 10.0


class User:
    def __init__(self, id: int, type: str, generations: int):
        # Location
        self.x = random.uniform(0, X_area)
        self.y = random.uniform(0, Y_area)
        self.rate_factor = 1.0
        # Initialize user attributes
        self.id = id
        self.round = 0
        self.type = type
        self.is_buyer = True
        self.is_seller = lambda: not self.is_buyer
        # in bits
        self.last_loss = 0
        self.next_loss = lambda: self.last_loss
        self.trading_amount = 0
        self.max_buffer = 1_000_000_000
        self.emp_buffer = random.uniform(30_000_000, 70_000_000)
        self.ocu_buffer = lambda: self.max_buffer - self.emp_buffer
        # LR user tends to keep more resources
        if type == "HB":
            self.willingness_to_keep = random.uniform(21.0, 23.0)
            self.assigned_blocks = 40000
            # Min 10Mb/s, Max 15Mb/s, Avg 10.8Mb/s
            self.demand = ParetoGenerator(
                100_000_000, 150_000_000, 108_000_000
            ).generate(generations)
        elif type == "LR":
            self.willingness_to_keep = random.uniform(23.0, 25.0)
            self.assigned_blocks = 4000
            # Min 1Mb, Max 10Mb, Avg 1.1Mb
            self.demand = ParetoGenerator(10_000_000, 100_000_000, 11_000_000).generate(
                generations
            )
        # Record the last loss and waste
        self.loss_counter = 0
        self.waste_counter = 0
        self.loss_amount_counter = 0
        self.waste_amount_counter = 0
        # history of attributes
        self.emp_buffer_rec = [self.emp_buffer]
        # self.utility_rec = [self.absolute_utility(0)]
        self.bid_rec = []
        self.payoff_rec = []
        self.utility_rec = []
        self.expected_price_rec = [self.expected_price()]
        self.role_rec = ["Buyer" if self.is_buyer else "Seller"]

    def record_current_state(self) -> None:
        if self.last_loss > 0:
            self.loss_counter += 1
            self.loss_amount_counter += self.last_loss
        if self.last_waste > 0:
            self.waste_counter += 1
            self.waste_amount_counter += self.last_waste
        # Record the current state of the user
        self.emp_buffer_rec.append(self.emp_buffer)
        # self.utility_rec.append(self.absolute_utility(0))
        self.expected_price_rec.append(self.expected_price())
        self.role_rec.append("Buyer" if self.is_buyer else "Seller")

    # Random waypoint generation
    def calculate_next_position(current_x, current_y, speed):
        """
        Calculates the next position of a user based on a Simple Random Walk model.
        The user moves a distance equal to 'speed' in a random direction.

        Args:
            current_x (float): The user's current x-coordinate (0 <= x <= 100).
            current_y (float): The user's current y-coordinate (0 <= y <= 100).
            speed (float): The distance the user moves in this step.

        Returns:
            tuple: A tuple containing:
                - next_x (float): The calculated next x-coordinate (clamped to [0, 100]).
                - next_y (float): The calculated next y-coordinate (clamped to [0, 100]).
        """

        # Choose a random direction (angle in radians)
        angle_radians = random.uniform(0, 2 * math.pi)

        # Calculate the displacement in x and y based on speed and angle
        delta_x = speed * math.cos(angle_radians)
        delta_y = speed * math.sin(angle_radians)

        # Calculate the potential next position
        potential_next_x = current_x + delta_x
        potential_next_y = current_y + delta_y

        # Clamp the next position to stay within the [0, 100] boundary
        # If the movement takes the user out of bounds, they stop at the boundary.
        next_x = max(0.0, min(X_area, potential_next_x))
        next_y = max(0.0, min(Y_area, potential_next_y))

        # Note: This simple clamping might cause users to 'slide' along boundaries
        # if they hit a corner. More complex boundary handling (e.g., reflection)
        # is possible but adds complexity. This version keeps it simple.

        return next_x, next_y

    def update(self) -> float:

        # calculate the data rate (bit/s) between a user and the broker
        def calculate_data_rate():
            self.x, self.y = User.calculate_next_position(self.x, self.y, 10.0)
            # Calculate wavelength (lambda = c / f)
            wavelength = c / frequency
            # Compute received power using the Friis transmission equation
            # Assume unit gains for both transmit and receive antennas
            # P_r = P_t * (λ / (4πd))^2
            received_power = (
                transmission_power
                * (
                    wavelength
                    / (
                        4
                        * math.pi
                        * math.sqrt(
                            (X_broker - self.x) ** 2 + (Y_broker - self.y) ** 2 + H**2
                        )
                    )
                )
                ** 2
            )
            # Calculate Signal-to-Noise Ratio (SNR)
            snr = received_power / noise
            # Use Shannon-Hartley theorem: C = B * log2(1 + SNR)
            data_rate = (
                (self.assigned_blocks + self.trading_amount)
                * bandwidth
                / 2000
                * math.log2(1 + snr)
            )
            return data_rate, bandwidth / 2000 * math.log2(1 + snr)

        self.last_arrival, self.rate_factor = calculate_data_rate()
        self.last_arrival = self.demand[self.round] - self.last_arrival
        self.round += 1
        self.last_loss = max(0, self.last_arrival - self.emp_buffer)
        self.last_waste = max(0, -self.last_arrival - self.ocu_buffer())
        self.emp_buffer = max(
            0, min(self.max_buffer, self.emp_buffer - self.last_arrival)
        )
        if self.emp_buffer == 0:
            pass

    def utility(self, demand: float) -> float:
        # Concave, strictly increasing, and continuously differentiable
        # utility(0) = 0, domain: [emp_buffer - max_buffer, +∞)
        def f(x):
            return math.sqrt(x * self.rate_factor + self.max_buffer - self.next_loss())

        return self.willingness_to_keep * (f(demand) - f(0.0))

    def absolute_utility(self, amount: float) -> float:
        return self.willingness_to_keep * math.sqrt(
            amount * self.rate_factor + self.max_buffer - self.next_loss()
        )

    def expected_price(self) -> float:
        # Calculate the expected price based on the user's empty buffer
        return (
            0.5 / math.sqrt(self.emp_buffer + self.max_buffer - self.next_loss())
        ) * self.willingness_to_keep

    def payoff_as_buyer(self, bid: float, price: float, total_supply: float) -> float:
        # Calculate the payoff based on the bid, price, and total supply
        # return self.utility(bid / price) - bid
        amount = bid / price
        fArea, err = integrate.quad(self.utility, 0, amount)
        return (
            (1 - (amount / total_supply)) * self.utility(amount)
            + (fArea / total_supply)
            - bid
        )

    def payoff_as_seller(self, bid: float, price: float, total_supply: float) -> float:
        # Calculate the payoff based on the bid, price, and total supply
        amount = self.assigned_blocks - bid / price
        fArea, err = integrate.quad(self.utility, -amount, 0)
        return (
            self.assigned_blocks * price
            - bid
            + (1 + (amount / (total_supply - self.assigned_blocks)))
            * self.utility(-amount)
            + (fArea / (total_supply - self.assigned_blocks))
        )

    def find_optimal_bid_as_buyer(self, price: float, total_supply: float) -> None:
        objective = lambda bid: -self.payoff_as_buyer(bid, price, total_supply)
        result = minimize_scalar(
            objective, bounds=(0.0, total_supply * price), method="bounded"
        )
        if result.success:
            self.bid = result.x
        else:
            raise ValueError("Failed to find an optimal bid (buyer)")

    def find_optimal_bid_as_seller(self, price: float, total_supply: float) -> None:
        objective = lambda bid: -self.payoff_as_seller(bid, price, total_supply)
        result = minimize_scalar(
            objective, bounds=(0.0, self.assigned_blocks * price), method="bounded"
        )
        if result.success:
            self.bid = result.x
        else:
            raise ValueError("Failed to find an optimal bid (seller)")
