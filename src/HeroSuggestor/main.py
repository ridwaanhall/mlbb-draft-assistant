import argparse
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MultiLabelBinarizer
import joblib

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'data', 'csv', 'hero_data.csv')
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'hero_suggestor_model.pkl')

MAX_TEAM = 4
MAX_BAN = 5
MAX_ENEMY = 5

# Hero ID to Name mapping
HERO_ID_TO_NAME = {
    1: 'Miya', 2: 'Balmond', 3: 'Saber', 4: 'Alice', 5: 'Nana', 6: 'Tigreal', 7: 'Alucard', 8: 'Karina', 9: 'Akai', 10: 'Franco',
    11: 'Bane', 12: 'Bruno', 13: 'Clint', 14: 'Rafaela', 15: 'Eudora', 16: 'Zilong', 17: 'Fanny', 18: 'Layla', 19: 'Minotaur', 20: 'Lolita',
    21: 'Hayabusa', 22: 'Freya', 23: 'Gord', 24: 'Natalia', 25: 'Kagura', 26: 'Chou', 27: 'Sun', 28: 'Alpha', 29: 'Ruby', 30: 'YSS',
    31: 'Moskov', 32: 'Johnson', 33: 'Cyclops', 34: 'Estes', 35: 'Hilda', 36: 'Aurora', 37: 'Lapu-Lapu', 38: 'Vexana', 39: 'Roger', 40: 'Karrie',
    41: 'Gatotkaca', 42: 'Harley', 43: 'Irithel', 44: 'Grock', 45: 'Argus', 46: 'Odette', 47: 'Lancelot', 48: 'Diggie', 49: 'Hylos', 50: 'Zhask',
    51: 'Helcurt', 52: 'Pharsa', 53: 'Lesley', 54: 'Jawhead', 55: 'Angela', 56: 'Gusion', 57: 'Valir', 58: 'Martis', 59: 'Uranus', 60: 'Hanabi',
    61: "Chang'e", 62: 'Kaja', 63: 'Selena', 64: 'Aldous', 65: 'Claude', 66: 'Vale', 67: 'Leomord', 68: 'Lunox', 69: 'Hanzo', 70: 'Belerick',
    71: 'Kimmy', 72: 'Thamuz', 73: 'Harith', 74: 'Minsitthar', 75: 'Kadita', 76: 'Faramis', 77: 'Badang', 78: 'Khufra', 79: 'Granger', 80: 'Guinevere',
    81: 'Esmeralda', 82: 'Terizla', 83: 'XBorg', 84: 'Ling', 85: 'Dyrroth', 86: 'Lylia', 87: 'Baxia', 88: 'Masha', 89: 'Wanwan', 90: 'Silvanna',
    91: 'Cecilion', 92: 'Carmilla', 93: 'Atlas', 94: 'Popol and Kupa', 95: 'Yu Zhong', 96: 'Luo Yi', 97: 'Benedetta', 98: 'Khaleed', 99: 'Barats', 100: 'Brody',
    101: 'Yve', 102: 'Mathilda', 103: 'Paquito', 104: 'Gloo', 105: 'Beatrix', 106: 'Phoveus', 107: 'Natan', 108: 'Aulus', 109: 'Aamon', 110: 'Valentina',
    111: 'Edith', 112: 'Floryn', 113: 'Yin', 114: 'Melissa', 115: 'Xavier', 116: 'Julian', 117: 'Fredrinn', 118: 'Joy', 119: 'Novaria', 120: 'Arlott',
    121: 'Ixia', 122: 'Nolan', 123: 'Cici', 124: 'Chip', 125: 'Zhuxin', 126: 'Suyou', 127: 'Lukas', 128: 'Kalea'
}
# Build a reverse mapping for name (lowercase, no spaces) -> id
HERO_NAME_TO_ID = {v.lower().replace(' ', '').replace("'", ""): k for k, v in HERO_ID_TO_NAME.items()}

def parse_args():
    parser = argparse.ArgumentParser(description='MLBB Hero Suggestor')
    parser.add_argument('--train', action='store_true', help='Train and save the model')
    parser.add_argument('--team_pick', type=str, help='Comma-separated hero IDs picked by your team (min 1, max 4)')
    parser.add_argument('--team_ban', type=str, default='', help='Comma-separated hero IDs banned by your team (max 5)')
    parser.add_argument('--enemy_pick', type=str, help='Comma-separated hero IDs picked by enemy team (min 1, max 5)')
    parser.add_argument('--enemy_ban', type=str, default='', help='Comma-separated hero IDs banned by enemy team (max 5)')
    parser.add_argument('--suggest', type=int, default=5, help='Number of hero suggestions to output')
    return parser.parse_args()

def load_data():
    df = pd.read_csv(CSV_PATH)
    return df

def prepare_training_data(df):
    # For each row, create training samples: (team, enemy, bans) -> main_heroid
    X, y = [], []
    for _, row in df.iterrows():
        # Use best1..best5 as positive samples for main_heroid synergy
        bests = [row[f'best{i+1}'] for i in range(5) if not pd.isna(row[f'best{i+1}'])]
        team = [row['main_heroid']]
        for best in bests:
            X.append(team)
            y.append(best)
        # Use counters as negative samples (optional, for more robust model)
        counters = [row[f'counter{i+1}'] for i in range(5) if not pd.isna(row[f'counter{i+1}'])]
        for counter in counters:
            X.append(team)
            y.append(counter)
    return X, y

def train_and_save_model():
    df = load_data()
    X, y = prepare_training_data(df)
    mlb = MultiLabelBinarizer(classes=range(1, 129))
    X_bin = mlb.fit_transform(X)
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_bin, y)
    joblib.dump({'model': clf, 'mlb': mlb}, MODEL_PATH)
    print('Model trained and saved.')

def load_model():
    if not os.path.exists(MODEL_PATH):
        print('Model not found. Please run with --train first to train the model.')
        exit(1)
    return joblib.load(MODEL_PATH)

def suggest_heroes(team_pick, team_ban, enemy_pick, enemy_ban, n_suggest):
    model_data = load_model()
    clf = model_data['model']
    mlb = model_data['mlb']
    all_heroes = set(clf.classes_)  # Only use heroes the model knows
    excluded = set(team_pick + team_ban + enemy_pick + enemy_ban)
    candidates = list(all_heroes - excluded)
    if len(candidates) < n_suggest:
        print(f"Warning: Only {len(candidates)} heroes available for suggestion (some heroes not in model/classes).")
    scores = []
    for hero in candidates:
        input_vec = mlb.transform([team_pick + [hero]])[0]
        prob = clf.predict_proba([input_vec])[0]
        hero_idx = clf.classes_.tolist().index(hero)
        score = prob[hero_idx]
        scores.append((hero, score))
    scores.sort(key=lambda x: x[1], reverse=True)
    return [h for h, _ in scores[:n_suggest]]

def parse_hero_arg(arg):
    """
    Accepts a comma-separated string of hero names or IDs.
    Returns a list of hero IDs.
    """
    result = []
    if not arg:
        return result
    for item in arg.split(','):
        item = item.strip()
        if not item:
            continue
        if item.isdigit():
            result.append(int(item))
        else:
            key = item.lower().replace(' ', '').replace("'", "")
            if key in HERO_NAME_TO_ID:
                result.append(HERO_NAME_TO_ID[key])
            else:
                print(f"Error: Hero '{item}' not recognized. Please check the name or use the hero ID.")
                exit(1)
    return result

def print_draft_table(team_pick, team_ban, enemy_pick, enemy_ban, suggestions):
    def hero_list(ids):
        return [HERO_ID_TO_NAME.get(i, str(i)) for i in ids]
    print("="*30)
    print("MLBB DRAFT ASSISTANT")
    print("-"*30)
    print("Team Ban:")
    for h in hero_list(team_ban):
        print(f"  {h}")
    print("Team Pick:")
    for h in hero_list(team_pick):
        print(f"  {h}")
    print("-"*30)
    print("Enemy Ban:")
    for h in hero_list(enemy_ban):
        print(f"  {h}")
    print("Enemy Pick:")
    for h in hero_list(enemy_pick):
        print(f"  {h}")
    print("="*30)
    print("Strong Recommended:")
    for idx, hid in enumerate(suggestions, 1):
        print(f"{idx}. {HERO_ID_TO_NAME.get(hid, str(hid))}")

def main():
    args = parse_args()
    if args.train:
        train_and_save_model()
        return
    if not (args.team_pick and args.enemy_pick):
        print('Error: --team_pick and --enemy_pick are required unless using --train.')
        exit(1)
    team_pick = parse_hero_arg(args.team_pick)
    team_ban = parse_hero_arg(args.team_ban)
    enemy_pick = parse_hero_arg(args.enemy_pick)
    enemy_ban = parse_hero_arg(args.enemy_ban)
    n_suggest = args.suggest
    suggestions = suggest_heroes(team_pick, team_ban, enemy_pick, enemy_ban, n_suggest)
    print_draft_table(team_pick, team_ban, enemy_pick, enemy_ban, suggestions)

if __name__ == '__main__':
    main()
