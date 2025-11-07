import math


def largest_remainder_method(values: list[float]) -> list[int]:
    """
    Apportions a list of floats into integers using the Largest Remainder Method.

    Ensures the sum of the returned integers equals the rounded sum of the
    original float values.

    Args:
        values: A list of floating-point numbers to be apportioned.

    Returns:
        A list of integers representing the apportioned values.
    """
    if not values:
        return []

    # --- 1. Calculate the Target Total Integer Amount ---
    # Round the total sum of the original values to the nearest integer.
    total_value = sum(values)
    target_sum = round(total_value)

    # --- 2. Initial Allocation (Floor) & Calculate Remainders ---
    integer_parts = [math.floor(v) for v in values]
    # Store remainders along with their original index to track them
    remainders = [(v - math.floor(v), i) for i, v in enumerate(values)]

    # --- 3. Calculate Initial Sum ---
    current_sum = sum(integer_parts)

    # --- 4. Determine the Difference ---
    difference = int(target_sum - current_sum)  # Ensure difference is integer

    # --- 5. Distribute Remaining Units ---
    # Sort indices based on remainders in descending order.
    # If remainders are equal, the original order (index) is preserved,
    # which acts as a simple tie-breaker.
    remainders.sort(key=lambda x: x[0], reverse=True)

    # Distribute the difference by adding 1 to the integer parts
    # corresponding to the largest remainders.
    for i in range(difference):
        # Get the index of the item with the i-th largest remainder
        index_to_increment = remainders[i][1]
        integer_parts[index_to_increment] += 1

    # --- 6. Return the final integer allocations ---
    return integer_parts


def calculate_initial_welfare(sellers, buyers) -> float:
    social_welfare = 0.0
    for buyer in buyers:
        social_welfare += buyer.absolute_utility(0)
    for seller in sellers:
        social_welfare += seller.absolute_utility(0)
    return social_welfare


def calculate_social_welfare(sellers, buyers) -> float:
    social_welfare = 0.0
    for buyer in buyers:
        social_welfare += buyer.absolute_utility(buyer.trading_amount)
    for seller in sellers:
        social_welfare += seller.absolute_utility(seller.trading_amount)
    return social_welfare


def optimal_bidding(buyers, sellers, initial_price, step_size):
    market_price = initial_price
    round_counter = 0
    local_price_rec = []
    local_demand_rec = []
    local_supply_rec = []
    local_welfare_rec = []
    delta_price = 100
    # while round_counter < 100:
    while abs(delta_price) > 1e-5:
        round_counter += 1
        total_bid = 0.0
        local_demand = 0.0
        local_supply = 0.0
        total_supply = 0.0

        for seller in sellers:
            total_supply += seller.assigned_blocks
        for buyer in buyers:
            buyer.find_optimal_bid_as_buyer(market_price, total_supply)
            buyer.payoff_rec.append(
                buyer.payoff_as_buyer(buyer.bid, market_price, total_supply)
            )
            buyer.utility_rec.append(buyer.utility(buyer.bid / market_price))
            buyer.bid_rec.append(buyer.bid)
            buyer.trading_amount = buyer.bid / market_price
            total_bid += buyer.bid
            local_demand += buyer.bid / market_price
        for seller in sellers:
            seller.find_optimal_bid_as_seller(market_price, total_supply)
            seller.payoff_rec.append(
                seller.payoff_as_seller(seller.bid, market_price, total_supply)
            )
            seller.utility_rec.append(
                seller.utility(seller.assigned_blocks - seller.bid / market_price)
            )
            seller.bid_rec.append(seller.bid)
            seller.trading_amount = seller.assigned_blocks - seller.bid / market_price
            total_bid += seller.bid
            local_supply += seller.assigned_blocks - seller.bid / market_price
        delta_price = (
            max(
                1e-2,
                market_price - 2e-6 * (total_supply - total_bid / market_price),
            )
            - market_price
        )
        market_price = max(
            1e-2,
            market_price - step_size * (total_supply - total_bid / market_price),
        )
        local_price_rec.append(market_price)
        local_demand_rec.append(local_demand)
        local_supply_rec.append(local_supply)
        local_welfare_rec.append(calculate_social_welfare(sellers, buyers))
    return (
        market_price,
        local_price_rec,
        local_demand_rec,
        local_supply_rec,
        local_welfare_rec,
    )
