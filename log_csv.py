import csv
import re

# Entrée et sortie
input_log = "checkpoints/2025-07-17T15-18-55/log"  # fichier log
output_csv = "CSV_YML/log.csv"  # fichier csv

with open(input_log, "r") as infile, open(output_csv, "w", newline="") as outfile:
    lines = [line.strip() for line in infile if line.strip()]
    
    # L’en-tête
    header_line = lines[0]
    headers = re.split(r'\s{2,}', header_line)
    writer = csv.writer(outfile)
    writer.writerow(headers)

    for line in lines[1:]:
        # Séparer les parties par au moins 2 espaces
        parts = re.split(r'\s{2,}', line)

        # Problème : parfois TimeDelta et Time sont collés avec un seul espace => corriger manuellement
        if len(parts) == 9:
            # On tente de séparer la 8e partie
            time_delta, time = parts[7].rsplit(" ", 1)
            parts = parts[:7] + [time_delta, time, parts[8]]
        elif len(parts) != 10:
            print(f"Ligne mal formatée : {line}")
            continue
        
        writer.writerow(parts)