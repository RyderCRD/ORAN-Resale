import os

mode_list = ["STATIC", "RANDOM", "HEURISTIC", "FUTURE"]

# Make sure the folders exist
for mode in mode_list:
    os.makedirs(f"./logs/{mode}", exist_ok=True)

setting_list = [
    {"slots": 1, "step_size": 1e-7, "generations": 2000},
    {"slots": 360, "step_size": 1e-6, "generations": 2000},
    {"slots": 4320, "step_size": 1e-6, "generations": 5000},
]
for mode in mode_list:
    for setting in setting_list:
        os.system(
            "python ./game.py"
            + " --mode "
            + str(mode)
            + " --slots "
            + str(setting["slots"])
            + " --step_size "
            + str(setting["step_size"])
            + " --generations "
            + str(setting["generations"])
            + " > ./logs/"
            + str(mode)
            + "/log.txt"
        )
