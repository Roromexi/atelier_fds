import csv
import os

# Fonction pour découper une ligne de log en liste de champs
def parse_log_line(line):
    return [item for item in line.strip().split()]

# Fonction pour nettoyer une ligne (ex. : retirer le symbole '%' à la fin de "Progression")
def clean_row(row):
    if row and '%' in row[-1]:
        row[-1] = row[-1].replace('%', '')
    return row

# Fonction pour lire le fichier CSV existant et récupérer les identifiants d'épisodes déjà présents
def get_existing_episodes(csv_file_path):
    existing_episodes = set()
    if os.path.exists(csv_file_path) and os.stat(csv_file_path).st_size > 0:
        with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                existing_episodes.add(row['Episode'])  # Utilise la colonne "Episode" comme identifiant unique
    return existing_episodes

# Fonction principale : lit le log, filtre les lignes déjà enregistrées, et met à jour le CSV
def log_to_csv(log_file_path, csv_file_path):
    with open(log_file_path, 'r', encoding='utf-8') as log_file:
        lines = [line for line in log_file if line.strip()]

    headers = parse_log_line(lines[0])
    data_lines = lines[1:]

    existing_episodes = get_existing_episodes(csv_file_path)

    new_rows = []
    for line in data_lines:
        row = clean_row(parse_log_line(line))
        episode_id = row[0]
        # Si l'épisode n'est pas encore dans le CSV, on l'ajoute à la liste
        if episode_id not in existing_episodes:
            new_rows.append(row)

    if not new_rows:
        print("✅ Aucune nouvelle ligne à ajouter.")
        return

    write_header = not os.path.exists(csv_file_path) or os.stat(csv_file_path).st_size == 0

    # Écriture dans le fichier CSV (mode append)
    with open(csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        if write_header:
            writer.writerow(headers)  
        writer.writerows(new_rows)  

    print(f"✅ {len(new_rows)} nouvelles lignes ajoutées à {csv_file_path}")


# -----------------------
# Exemple d'utilisation
# -----------------------
if __name__ == "__main__":
    
    fichier_log = "checkpoints/2025-07-18T08-08-12/log"
    fichier_csv = "CSV_YML/log.csv"
    
    # Lancer l'importation
    log_to_csv(fichier_log, fichier_csv)
