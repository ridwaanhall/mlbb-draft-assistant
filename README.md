# MLBB Draft Assistant

A machine learning-powered assistant for Mobile Legends: Bang Bang (MLBB) draft phase. This tool helps you make optimal hero picks based on your team's and the enemy's picks and bans, using real synergy and counter data.

## Features

- **Suggests the best heroes to pick** based on current draft state (team picks, bans, enemy picks, bans)
- **Supports both hero names and IDs** as input (case-insensitive, spaces and apostrophes ignored)
- **Easy command-line interface**
- **Fast predictions** (model is trained once and reused)
- **Clear, professional output** in table format

## Setup

1. **Install dependencies** (Python 3.8+ recommended):

   ```sh
   pip install pandas scikit-learn joblib
   ```

2. **Prepare your data**
   - Place your hero draft data in `data/csv/hero_data.csv` (see project for format).

## Usage

### 1. Train the Model

You must train the model before making suggestions:

```sh
python src/HeroSuggestor/main.py --train
```

### 2. Get Hero Suggestions

You can use either hero names or IDs (case-insensitive, spaces and apostrophes ignored):

```sh
python src/HeroSuggestor/main.py --team_pick miya,yve,nolan --team_ban suyou,lukas --enemy_pick kalea,chip --enemy_ban selena,ixia --suggest 10
```

**Example Output:**

```txt
==============================
MLBB DRAFT ASSISTANT
------------------------------
Team Ban:
  Suyou
  Lukas
Team Pick:
  Miya
  Yve
  Nolan
------------------------------
Enemy Ban:
  Selena
  Ixia
Enemy Pick:
  Kalea
  Chip
==============================
Strong Recommended:
1. HeroName1
2. HeroName2
...
```

## Arguments

- `--train` : Train and save the model (must be run first or after updating data)
- `--team_pick` : Comma-separated hero names or IDs picked by your team (min 1, max 4)
- `--team_ban` : Comma-separated hero names or IDs banned by your team (max 5)
- `--enemy_pick` : Comma-separated hero names or IDs picked by enemy team (min 1, max 5)
- `--enemy_ban` : Comma-separated hero names or IDs banned by enemy team (max 5)
- `--suggest` : Number of hero suggestions to output (default: 5)

## Notes

- The model will only suggest heroes it has seen in your data as possible picks.
- If you add or update your data, retrain the model with `--train`.
- Hero names are matched case-insensitively and with spaces/apostrophes ignored.

## License

Apache License 2.0
