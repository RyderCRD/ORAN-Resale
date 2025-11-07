from user import User
from tqdm import tqdm
import matplotlib.pyplot as plt
from tools import *
import random
import argparse

random.seed(2025)
SMALL_SIZE = 10
MEDIUM_SIZE = 14
BIG_SIZE = 15
plt.rc("font", size=BIG_SIZE)  # controls default text sizes
plt.rc("axes", titlesize=BIG_SIZE)  # fontsize of the axes title
plt.rc("axes", labelsize=BIG_SIZE)  # fontsize of the x and y labels
plt.rc("xtick", labelsize=BIG_SIZE)  # fontsize of the tick labels
plt.rc("ytick", labelsize=BIG_SIZE)  # fontsize of the tick labels
plt.rc("legend", fontsize=BIG_SIZE)  # legend fontsize
plt.rc("figure", titlesize=BIG_SIZE)  # fontsize of the figure title

parser = argparse.ArgumentParser(description="Construct SAGs")
parser.add_argument(
    "--mode",
    type=str,
    default="FUTURE",
)
parser.add_argument(
    "--slots",
    type=int,
    default=1,
)
parser.add_argument(
    "--step_size",
    type=float,
    default=1e-7,
)
parser.add_argument(
    "--generations",
    type=int,
    default=2000,
)

slots = parser.parse_args().slots
step_size = parser.parse_args().step_size
generations = parser.parse_args().generations
RANDOM = parser.parse_args().mode == "RANDOM"
STATIC = parser.parse_args().mode == "STATIC"
HEURISTIC = parser.parse_args().mode == "HEURISTIC"
FUTURE = parser.parse_args().mode == "FUTURE"

users = [User(i, "HB", generations) for i in range(1, 6)] + [
    User(j, "LR", generations) for j in range(6, 11)
]
if FUTURE:
    for user in users:
        user.next_loss = lambda: 10.0 * user.last_loss

price_rec = []
demand_rec = []
supply_rec = []
welfare_rec = []
clr_price_rec = []
market_clearing_welfare = []

for _ in tqdm(range(slots)):

    # Phase 1: Update the user's buffer
    for user in users:
        user.update()

    # print("Round:", _ + 1)
    # Calculate the average expected price as the initial market price
    initial_market_price = sum(user.expected_price() for user in users) / len(users)

    if RANDOM:
        buyers = random.sample(users, 5)
        for user in users:
            user.is_buyer = user in buyers
    else:
        # Determine the role of each user based on the market price
        for user in users:
            user.is_buyer = user.expected_price() > initial_market_price

    buyers = [user for user in users if user.is_buyer]
    sellers = [user for user in users if user.is_seller()]
    market_clearing_welfare.append(calculate_initial_welfare(sellers, buyers))
    welfare_rec.append(calculate_initial_welfare(sellers, buyers))

    if not STATIC:
        market_clearing_price = 0.0
        initial_market_price = 1.095
        ############### Do Trade ################
        if buyers and len(sellers) > 1:
            (
                market_clearing_price,
                local_price_rec,
                local_demand_rec,
                local_supply_rec,
                local_welfare_rec,
            ) = optimal_bidding(buyers, sellers, initial_market_price, step_size)
            price_rec += local_price_rec
            demand_rec += local_demand_rec
            supply_rec += local_supply_rec
            welfare_rec += local_welfare_rec

            # Round up
            buyer_amounts, seller_amounts = [], []
            original_amounts = []
            for user in users:
                if user.is_buyer:
                    buyer_amounts.append(user.bid / market_clearing_price)
                    original_amounts.append(user.bid / market_clearing_price)
                else:
                    seller_amounts.append(
                        user.bid / market_clearing_price - user.assigned_blocks
                    )
                    original_amounts.append(
                        user.bid / market_clearing_price - user.assigned_blocks
                    )
            buyer_int, seller_int = largest_remainder_method(
                buyer_amounts
            ), largest_remainder_method(seller_amounts)
            for user in users:
                if user.is_buyer:
                    user.trading_amount = buyer_int.pop(0)
                else:
                    user.trading_amount = seller_int.pop(0)
            # print("Amount", [user.trading_amount for user in users])

        # Record the market clearing price
        clr_price_rec.append(market_clearing_price)

        market_clearing_welfare[-1] = calculate_social_welfare(sellers, buyers)
        ############### Do Trade ################

    buyers = [user for user in users if user.is_buyer]
    sellers = [user for user in users if user.is_seller()]

    # Record the current state of each user
    for user in users:
        user.record_current_state()

# Output and plot results for specific settings
# Output the numerical results for 12 hours (4320 slots)
if slots == 4320:
    print("Loss counter:", sum([user.loss_counter for user in users]))
    print("Loss amount:", sum([user.loss_amount_counter for user in users]))
    print("Waste counter:", sum([user.waste_counter for user in users]))
    print("Waste amount:", sum([user.waste_amount_counter for user in users]))
    print("Total social welfare:", sum(market_clearing_welfare))
    print("Min_welfare:", min(market_clearing_welfare))

    for user in users:
        print(
            user.id,
            user.loss_counter,
            user.loss_amount_counter,
            user.waste_counter,
            user.waste_amount_counter,
            sum(user.utility_rec),
        )

# Plot the buffer and willingness trends for 1 hour (360 slots)
elif slots == 360:
    plt.plot([], linestyle="--", label="LR users", linewidth=2, color="black")
    plt.plot([], linestyle="-", label="HB users", linewidth=2, color="black")
    for user in users:
        if user.type == "LR":
            plt.plot(user.emp_buffer_rec, linestyle="--", linewidth=2)
        else:
            plt.plot(user.emp_buffer_rec, linestyle="-", linewidth=2)
    plt.xlabel("Number of Time Slots", fontsize=BIG_SIZE)
    plt.ylabel("Bits", fontsize=BIG_SIZE)
    plt.legend(loc="best", fontsize=MEDIUM_SIZE)
    plt.savefig(
        f"./logs/{parser.parse_args().mode}/" + "Empty Buffer Trend" + ".png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.clf()

    plt.plot([], linestyle="--", label="LR users", linewidth=2, color="black")
    plt.plot([], linestyle="-", label="HB users", linewidth=2, color="black")
    for user in users:
        if user.type == "LR":
            plt.plot(user.expected_price_rec, linestyle="--", linewidth=2)
        else:
            plt.plot(user.expected_price_rec, linestyle="-", linewidth=2)
    plt.gca().ticklabel_format(
        axis="y", style="sci", scilimits=(0, 0), useMathText=True
    )
    plt.xlabel("Number of Time Slots", fontsize=BIG_SIZE)
    plt.ylabel("Willingness to Buy", fontsize=BIG_SIZE)
    plt.legend(loc="best", fontsize=MEDIUM_SIZE)
    plt.savefig(
        f"./logs/{parser.parse_args().mode}/" + "Willingness Trend" + ".png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.clf()

# Plot the price, resource, and social welfare convergence for 1 slot
elif slots == 1:
    plt.plot(price_rec, label="Market Price", linewidth=2.5)
    plt.xlabel("Number of Iterations", fontsize=MEDIUM_SIZE)
    plt.ylabel("Unit Price", fontsize=MEDIUM_SIZE)
    plt.legend(loc="best", fontsize=BIG_SIZE)
    plt.savefig(
        f"./logs/{parser.parse_args().mode}/" + "Price Trend" + ".png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.clf()

    plt.plot(demand_rec[1:], linestyle="-", label="Resource Requesting", linewidth=1.5)
    plt.plot(supply_rec[1:], linestyle="--", label="Resource Sharing", linewidth=1.5)
    plt.xlabel("Number of Iterations", fontsize=MEDIUM_SIZE)
    plt.ylabel("Number of RBs", fontsize=MEDIUM_SIZE)
    plt.legend(loc="best", fontsize=BIG_SIZE)
    plt.savefig(
        f"./logs/{parser.parse_args().mode}/"
        + "Requested & Shared Resources Trend"
        + ".png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.clf()

    plt.plot(welfare_rec, label="Social Welfare", linewidth=2.5)
    plt.xlabel("Number of Iterations", fontsize=MEDIUM_SIZE)
    plt.ylabel("Utility Value", fontsize=MEDIUM_SIZE)
    plt.legend(loc="best", fontsize=BIG_SIZE)
    plt.savefig(
        f"./logs/{parser.parse_args().mode}/" + "Social Welfare Trend" + ".png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.clf()
