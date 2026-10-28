DEBUGGING RL
Check in order: (1) env by hand: random policy plus a scripted optimal path; (2) one-transition update test against hand math; (3) compare with the value-iteration oracle; (4) exploration schedule; (5) hyperparameters.
Top suspects: bootstrapping from terminal states, swapped (row, col), terminated vs truncated mix-up.
