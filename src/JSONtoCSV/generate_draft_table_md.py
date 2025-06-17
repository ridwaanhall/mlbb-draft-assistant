import pandas as pd
import os

# Hero ID to Name mapping (copied from main.py for standalone use)
HERO_ID_TO_NAME = {
    1: 'Miya', 2: 'Balmond', 3: 'Saber', 4: 'Alice', 5: 'Nana', 6: 'Tigreal', 7: 'Alucard', 8: 'Karina', 9: 'Akai', 10: 'Franco',
    11: 'Bane', 12: 'Bruno', 13: 'Clint', 14: 'Rafaela', 15: 'Eudora', 16: 'Zilong', 17: 'Fanny', 18: 'Layla', 19: 'Minotaur', 20: 'Lolita',
    21: 'Hayabusa', 22: 'Freya', 23: 'Gord', 24: 'Natalia', 25: 'Kagura', 26: 'Chou', 27: 'Sun', 28: 'Alpha', 29: 'Ruby', 30: 'Yi Sun-shin',
    31: 'Moskov', 32: 'Johnson', 33: 'Cyclops', 34: 'Estes', 35: 'Hilda', 36: 'Aurora', 37: 'Lapu-Lapu', 38: 'Vexana', 39: 'Roger', 40: 'Karrie',
    41: 'Gatotkaca', 42: 'Harley', 43: 'Irithel', 44: 'Grock', 45: 'Argus', 46: 'Odette', 47: 'Lancelot', 48: 'Diggie', 49: 'Hylos', 50: 'Zhask',
    51: 'Helcurt', 52: 'Pharsa', 53: 'Lesley', 54: 'Jawhead', 55: 'Angela', 56: 'Gusion', 57: 'Valir', 58: 'Martis', 59: 'Uranus', 60: 'Hanabi',
    61: "Chang'e", 62: 'Kaja', 63: 'Selena', 64: 'Aldous', 65: 'Claude', 66: 'Vale', 67: 'Leomord', 68: 'Lunox', 69: 'Hanzo', 70: 'Belerick',
    71: 'Kimmy', 72: 'Thamuz', 73: 'Harith', 74: 'Minsitthar', 75: 'Kadita', 76: 'Faramis', 77: 'Badang', 78: 'Khufra', 79: 'Granger', 80: 'Guinevere',
    81: 'Esmeralda', 82: 'Terizla', 83: 'X.Borg', 84: 'Ling', 85: 'Dyrroth', 86: 'Lylia', 87: 'Baxia', 88: 'Masha', 89: 'Wanwan', 90: 'Silvanna',
    91: 'Cecilion', 92: 'Carmilla', 93: 'Atlas', 94: 'Popol and Kupa', 95: 'Yu Zhong', 96: 'Luo Yi', 97: 'Benedetta', 98: 'Khaleed', 99: 'Barats', 100: 'Brody',
    101: 'Yve', 102: 'Mathilda', 103: 'Paquito', 104: 'Gloo', 105: 'Beatrix', 106: 'Phoveus', 107: 'Natan', 108: 'Aulus', 109: 'Aamon', 110: 'Valentina',
    111: 'Edith', 112: 'Floryn', 113: 'Yin', 114: 'Melissa', 115: 'Xavier', 116: 'Julian', 117: 'Fredrinn', 118: 'Joy', 119: 'Novaria', 120: 'Arlott',
    121: 'Ixia', 122: 'Nolan', 123: 'Cici', 124: 'Chip', 125: 'Zhuxin', 126: 'Suyou', 127: 'Lukas', 128: 'Kalea'
}

# Fix: Use project root, not script dir
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
except NameError:
    PROJECT_ROOT = os.getcwd()

CSV_PATH = os.path.join(PROJECT_ROOT, 'data', 'csv', 'hero_data.csv')
OUTPUT_PATH = os.path.join(PROJECT_ROOT, 'DRAFT_TABLE.md')

SECTION_CONFIGS = [
    {
        'title': 'A. Counter',
        'desc': 'These columns show which heroes are strong against the main hero (counters).',
        'cols': ['main_heroid', 'counter1', 'counter2', 'counter3', 'counter4', 'counter5'],
        'header': ['main_hero', 'counter1', 'counter2', 'counter3', 'counter4', 'counter5']
    },
    {
        'title': 'B. Countered',
        'desc': 'These columns show which heroes are most easily countered by the main hero.',
        'cols': ['main_heroid', 'countered1', 'countered2', 'countered3', 'countered4', 'countered5'],
        'header': ['main_hero', 'countered1', 'countered2', 'countered3', 'countered4', 'countered5']
    },
    {
        'title': 'C. Best (Synergy)',
        'desc': 'These columns show which heroes have the best synergy with the main hero.',
        'cols': ['main_heroid', 'best1', 'best2', 'best3', 'best4', 'best5'],
        'header': ['main_hero', 'best1', 'best2', 'best3', 'best4', 'best5']
    },
    {
        'title': 'D. Worst (Synergy)',
        'desc': 'These columns show which heroes have the worst synergy with the main hero.',
        'cols': ['main_heroid', 'worst1', 'worst2', 'worst3', 'worst4', 'worst5'],
        'header': ['main_hero', 'worst1', 'worst2', 'worst3', 'worst4', 'worst5']
    }
]

def id_to_name(val):
    try:
        return HERO_ID_TO_NAME[int(val)]
    except Exception:
        return str(val)

def section_to_markdown(df, config):
    lines = []
    lines.append(f"## {config['title']}")
    lines.append("")
    lines.append(config['desc'])
    lines.append("")
    lines.append('| ' + ' | '.join(config['header']) + ' |')
    lines.append('|' + '---|' * len(config['header']))
    for _, row in df[config['cols']].iterrows():
        names = [id_to_name(row[c]) for c in config['cols']]
        lines.append('| ' + ' | '.join(names) + ' |')
    lines.append("")
    return '\n'.join(lines)

def main():
    df = pd.read_csv(CSV_PATH)
    md_lines = [
        '# MLBB Draft Table Documentation',
        '',
        'This document provides a full, human-readable reference for the columns in `hero_data.csv` used by the MLBB Draft Assistant. All hero IDs are replaced with their actual names for clarity.',
        '',
        '---',
        ''
    ]
    for config in SECTION_CONFIGS:
        md_lines.append(section_to_markdown(df, config))
    md_lines.append('For the full list of hero names and their IDs, see the mapping in your codebase or documentation.')
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))
    print(f"Draft table documentation generated at {OUTPUT_PATH}")

if __name__ == '__main__':
    main()
