'''
This script processes hero counter and compatibility data from JSON files
and exports it to a CSV file.
'''
import json
import csv
import os

def extract_hero_ids_from_list(hero_data_list, num_heroes=5):
    """
    Extracts 'heroid' from a list of hero dictionaries.
    Pads with None if fewer than num_heroes are found.
    """
    ids = []
    if isinstance(hero_data_list, list):
        for hero_item in hero_data_list[:num_heroes]: # Iterate only up to num_heroes
            if isinstance(hero_item, dict):
                ids.append(hero_item.get('heroid'))
            else:
                ids.append(None) 
    # Pad with None if fewer than num_heroes were extracted
    while len(ids) < num_heroes:
        ids.append(None)
    return ids

def process_single_hero_files(counter_json_path, compatibility_json_path):
    """
    Reads and processes JSON files for a single hero.
    Returns a list representing a data row for the CSV, or None on error.
    """
    try:
        with open(counter_json_path, 'r', encoding='utf-8') as f:
            counter_data_full = json.load(f)
        with open(compatibility_json_path, 'r', encoding='utf-8') as f:
            compatibility_data_full = json.load(f)
    except FileNotFoundError:
        # Error message will be printed in the main loop
        return None
    except json.JSONDecodeError:
        # Error message will be printed in the main loop
        return None

    try:
        if not (counter_data_full.get('data') and counter_data_full['data'].get('records') and
                compatibility_data_full.get('data') and compatibility_data_full['data'].get('records')):
            return None # Indicates missing primary keys
        
        if not counter_data_full['data']['records'] or not compatibility_data_full['data']['records']:
            return None # Indicates empty records

        counter_record_data = counter_data_full['data']['records'][0].get('data', {})
        compatibility_record_data = compatibility_data_full['data']['records'][0].get('data', {})

        main_heroid = counter_record_data.get('main_heroid')
        if main_heroid is None:
            main_heroid = compatibility_record_data.get('main_heroid')
        
        if main_heroid is None:
            return None # main_heroid is crucial
        
        counters = extract_hero_ids_from_list(counter_record_data.get('sub_hero', []), 5)
        countered_by = extract_hero_ids_from_list(counter_record_data.get('sub_hero_last', []), 5)
        best_with = extract_hero_ids_from_list(compatibility_record_data.get('sub_hero', []), 5)
        worst_with = extract_hero_ids_from_list(compatibility_record_data.get('sub_hero_last', []), 5)

        return [main_heroid] + counters + countered_by + best_with + worst_with

    except (KeyError, IndexError, TypeError):
        # Error message will be printed in the main loop, including main_heroid if available
        hero_id_for_error = 'unknown'
        if 'main_heroid' in locals() and main_heroid is not None:
            hero_id_for_error = main_heroid
        elif 'counter_record_data' in locals() and counter_record_data.get('main_heroid') is not None:
            hero_id_for_error = counter_record_data.get('main_heroid')
        # print(f"Warning: Data structure error for hero ID {hero_id_for_error}.") # Example of more detailed internal logging
        return None

if __name__ == "__main__":
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(script_dir, '..', '..')) # Navigates two levels up to the project root
    except NameError: 
        # __file__ is not defined if, for example, the script is run in an environment
        # where it's not available (e.g. an interactive interpreter pasting code).
        # Fallback to current working directory as a potential project root.
        project_root = os.getcwd()
        print(f"Warning: __file__ not defined. Assuming project root is current working directory: {project_root}")

    # Define output CSV file path as requested: in "data/csv" folder
    csv_output_dir = os.path.join(project_root, 'data', 'csv')
    output_csv_file_path = os.path.join(csv_output_dir, "hero_data.csv")

    if not os.path.exists(csv_output_dir):
        try:
            os.makedirs(csv_output_dir)
            print(f"Created output directory: {csv_output_dir}")
        except OSError as e:
            print(f"Error creating output directory {csv_output_dir}: {e}")
            exit() 

    header = ['main_heroid'] + \
             [f'counter{i+1}' for i in range(5)] + \
             [f'countered{i+1}' for i in range(5)] + \
             [f'best{i+1}' for i in range(5)] + \
             [f'worst{i+1}' for i in range(5)]
    
    all_hero_data_rows = []
    num_heroes_to_process = 128 
    processed_count = 0
    skipped_count = 0

    print(f"Starting processing for up to {num_heroes_to_process} heroes...")

    for hero_id in range(1, num_heroes_to_process + 1):
        counter_json_file = os.path.join(project_root, 'data', 'hero_counter', f'{hero_id}.json')
        compatibility_json_file = os.path.join(project_root, 'data', 'hero_compatibility', f'{hero_id}.json')
        
        hero_data_row = process_single_hero_files(counter_json_file, compatibility_json_file)
        
        if hero_data_row:
            all_hero_data_rows.append(hero_data_row)
            processed_count += 1
        else:
            skipped_count += 1
            print(f"Skipping hero ID: {hero_id}. Problem with files or data structure. Paths checked:")
            print(f"  Counter: {counter_json_file}")
            print(f"  Compatibility: {compatibility_json_file}")

    if not all_hero_data_rows:
        print("No data was successfully processed. CSV file will not be created or will be empty.")
    else:
        try:
            with open(output_csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(header)
                writer.writerows(all_hero_data_rows)
            print(f"Successfully created CSV: {output_csv_file_path}")
            print(f"Total heroes processed and added to CSV: {processed_count}")
            if skipped_count > 0:
                print(f"Total heroes skipped due to errors: {skipped_count}")
        except IOError as e:
            print(f"Error: Could not write to CSV file at {output_csv_file_path}: {e}")
