import csv
import os

def append_row_to_csv(row: dict, filepath: str = "dataset.csv") -> None:
    """Append a single row to the CSV dataset file."""
    file_exists = os.path.isfile(filepath)
    
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        
        # Scrivi header solo se il file non esiste ancora
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(row)