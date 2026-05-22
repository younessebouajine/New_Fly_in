*This project has been created as part of the 42 curriculum by [ybouaji].*

---

# Drone Swarm Pathfinder

## Description

Drone Swarm Pathfinder is a multi-agent drone routing simulation. Given a map of interconnected zones, it computes optimal paths for a fleet of drones to travel from a start hub to an end hub, respects zone and link capacity constraints, handles special zone types (blocked, restricted, priority), and visualizes every move turn-by-turn in the terminal with rich color output.

The goal of the project is to model a real-world constraint-satisfaction routing problem: how do you efficiently move multiple agents across a shared network when nodes and edges have limited capacity, some routes are faster than others, and some zones impose travel penalties?

---

## Instructions

### Requirements

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (fast Python package manager)

### Installation

```bash
uv sync
```

### Running the simulation

The program reads a map from `file.txt` by default:

```bash
make run
```

To run with a custom map file, edit the `FILE` variable in the `Makefile`, or call directly:

```bash
uv run python3 main.py
```

### Other commands

| Command       | Description                          |
|---------------|--------------------------------------|
| `make install` | Install dependencies via `uv sync`  |
| `make run`     | Run the simulation                  |
| `make debug`   | Run under Python's `pdb` debugger   |
| `make lint`    | Run `flake8` + `mypy` type checks   |
| `make clean`   | Remove `__pycache__` and mypy cache |

---

## Map File Format

The input file defines the number of drones, zones, and connections between them.

```
nb_drones: 3

start_hub: start_hub 0 0 [color=green]
hub: alpha 1 0 [max_drones=2 color=blue]
hub: beta  0 1 [zone=restricted color=orange]
hub: gamma 1 1 [zone=priority color=yellow]
end_hub: end_hub 2 1 [color=red]

connection: start_hub - alpha [max_link_capacity=2]
connection: start_hub - beta
connection: alpha - gamma
connection: beta  - gamma
connection: gamma - end_hub
```

### Zone types

| Type         | Description                                        | Cost |
|--------------|----------------------------------------------------|------|
| `normal`     | Standard zone; default                             | 1    |
| `priority`   | Fast lane; preferred by pathfinder                 | 1    |
| `restricted` | Adds a one-turn delay; drone enters over 2 turns   | 2    |
| `blocked`    | Impassable; pathfinder skips entirely              | —    |

### Metadata keys

**Zone:** `zone=<type>`, `color=<css-name|#hex|rainbow>`, `max_drones=<int>`

**Connection:** `max_link_capacity=<int>` (default 1)

---

## Example Input and Expected Output

**`file.txt`**
```
nb_drones: 2

start_hub: A 0 0
hub: B 1 0 [color=cyan]
hub: C 0 1 [zone=restricted color=orange]
end_hub: D 1 1 [color=red]

connection: A - B
connection: A - C
connection: B - D
connection: C - D
```

**Terminal output**
```
=== SIMULATION START ===

==> TURN 1 <==

D1-B  D2-A->C

==> TURN 2 <==

D1-D  D2-C

==> TURN 3 <==

D2-D

TOTAL TURNS: 3

=== SIMULATION FINISHED ===
```

Drone 1 takes the direct path A → B → D (2 turns).  
Drone 2 takes the longer restricted path A → C → D (3 turns, because the restricted zone adds one waiting turn).

---

## Algorithm Explanation

### Path assignment strategy

Paths are computed once before the simulation begins by `PathFinder.find_all_paths()`. The algorithm runs a **penalized Dijkstra** multiple times — once per drone — and accumulates zone-use penalties after each pass to push subsequent drones toward different routes.

**Steps:**

1. Run Dijkstra from `start` to `end` with the current penalty map.
2. If the resulting path is new (not a duplicate of a previous one), record it.
3. For every intermediate zone on that path, add `+4` to its penalty weight.
4. Repeat for each drone.
5. After all paths are found, keep at most the **two cheapest distinct paths** (sorted by total base cost), and distribute drones across them round-robin.

**Why penalized Dijkstra?**

Pure Dijkstra always returns the same single cheapest path. By inflating the cost of already-chosen zones, successive drones are naturally steered toward alternative routes — achieving load distribution without a combinatorial multi-agent search.

**Move cost per zone type:**

| Zone type   | Cost |
|-------------|------|
| `priority`  | 1.0  |
| `normal`    | 1.0  |
| `restricted`| 2.0  |
| `blocked`   | ∞ (skipped) |

### Simulation loop

Each turn, `Simulation.move_drones()` processes all drones in order:

- Drones that have already reached the end zone are skipped.
- Drones with `turns_remaining > 0` (mid-transit through a restricted zone) tick down their counter; they "arrive" when it reaches zero.
- A drone that is ready to move checks, in order:
  1. Is the next zone `blocked`? → skip.
  2. Is the next zone already reserved by another drone this turn? → wait.
  3. Is the next zone at full capacity (`max_drones`)? → wait.
  4. Does the connecting link have capacity remaining (`max_link_capacity`)? → wait if not.
- If all checks pass, the drone moves. For restricted zones, the physical arrival is deferred by one turn.
- Connection transit counts are reset at the end of every turn.

### Design decisions

- **At most two paths** are retained to keep the simulation deterministic and readable for small fleets. A single path is used when no alternative exists.
- **Reserved zones** (per-turn set) prevent two drones from colliding into the same zone in the same turn, even if capacity would technically allow it.
- **Restricted zones use a two-turn model**: the drone leaves its current zone immediately (removing itself from capacity), but only "lands" in the restricted zone after one extra turn. This models a slow approach corridor.

---

## Visual Representation

The simulation uses the [Rich](https://github.com/Textualize/rich) library for terminal rendering and a custom `Colorizer` class (`colors.py`) backed by [webcolors](https://pypi.org/project/webcolors/).

### Features

- **Per-zone colors** — each zone can be assigned any CSS named color (e.g. `cyan`, `tomato`, `goldenrod`) or a hex code (`#ff8800`). Colors are resolved to hex at parse time and applied via Rich markup tags (`[#rrggbb]text[/]`).
- **Drone labels** — drones are always displayed in cyan (`D1`, `D2`, …) for instant visual distinction from zone names.
- **Rainbow mode** — a zone can declare `color=rainbow`, which cycles through the visible spectrum character-by-character, making special landmark zones immediately eye-catching.
- **Restricted-zone arrow notation** — when a drone begins entering a restricted zone, it is shown as `D1-alpha->restricted_zone`, making the in-transit state explicit rather than invisible.
- **Turn headers** — each turn is clearly delimited with `==> TURN N <==`, and the overall session is wrapped with `=== SIMULATION START ===` / `=== SIMULATION FINISHED ===`.

Together these choices make it easy to follow several drones simultaneously: the consistent cyan drone labels draw the eye, zone colors provide spatial memory, and the arrow notation makes blocked/delayed movement immediately understandable without referring back to the map file.

---

## Resources

### Pathfinding

- [Dijkstra's Algorithm — Youtube](https://youtu.be/NpJqtN2X9Qw?si=pVftF_Kj8n3bLa-U)
- [Dijkstra's Algorithm — Wikipedia](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
- [Dijkstra's Algorithm — GeeksforGeeks](https://www.geeksforgeeks.org/dsa/dijkstras-shortest-path-algorithm-greedy-algo-7/)
- [Multi-Agent Pathfinding — overview](https://en.wikipedia.org/wiki/Multi-agent_pathfinding)
- [Multi-Agent Pathfinding — w3schools](https://www.w3schools.com/dsa/dsa_algo_graphs_dijkstra.php)

### Python libraries

- [Rich — terminal formatting](https://rich.readthedocs.io/en/stable/)
- [webcolors — CSS color names](https://pypi.org/project/webcolors/)
- [uv — Python package manager](https://github.com/astral-sh/uv)
- [heapq — Python priority queue](https://docs.python.org/3/library/heapq.html)

### How AI was used

AI was used to assist with:

- **Algorithm review** — sanity-checking the penalized Dijkstra approach and the turn-based simulation loop logic.
- **Code suggestions** — minor refactoring hints for the `Simulation.move_drones` method and the `Colorizer` class. and explain some steps in djikstra of it helps me devided my project and give me some hints when i finds some hard errors
 
 thanks for your read this file