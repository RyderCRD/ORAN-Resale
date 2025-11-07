The development of the Open RAN (O-RAN) framework helps enable network slicing through its virtualization, interoperability, and flexibility. To improve spectral efficiency and better meet users' dynamic and heterogeneous service demands, O-RAN's flexibility further presents an opportunity for resource reselling of unused physical resource blocks (PRBs) across users. In this work, we propose a novel game-based user-to-user PRB reselling model in the O-RAN setting, which models the carryover of unmet demand across time slots, along with how users' internal buffer states relate to any PRBs purchased. We formulate the interplay between the users as a strategic game, with each participant aiming to maximize their own payoffs, and we prove the existence and uniqueness of the Nash equilibrium (NE) in the game. We furthermore propose an iterative bidding mechanism that converges to this NE. Extensive simulations demonstrate that our proposed approach reduces data loss by 30.5% and spectrum resource wastage by 50.7%, while significantly improving social welfare compared to its absence.

## Reproduction
Required Python libs: scipy, matplotlib, tqdm.

Clone this repository, enter the `'ORAN-Resale-main'` folder and execute:
```
python .\auto_run.py
```
You can then find all the results we demonstrated in our paper in the `'logs'` folder.

Please note that the 12-hour (4320 slots) simulation may require several hours to complete.

## Citation
Please cite [our paper](https://arxiv.org/abs/2509.19392) if you found this repository helpful.
```
@article{cao2025user,
  title={A User-to-User Resource Reselling Game in Open RAN with Buffer Rollover},
  author={Cao, Ruide and Siew, Marie and Yau, David},
  journal={arXiv preprint arXiv:2509.19392},
  year={2025}
}
```

## Contribution

Contributions are welcome! Please feel free to drop your issues and PRs :)
