import csv

def validate_file(file_contents):
    try:
        csv_reader = csv.reader(file_contents.splitlines())
        header = next(csv_reader, None)

        if header is not None and len(header) < 3:
            return "File should contain at least 3 columns with no header"

        for row in csv_reader:
            if len(row) < 3 or not str(row[2]).lstrip().isdigit():
                return "Data is not valid. Ensure there are at least 3 columns, and the third column can be converted to a positive integer."

        return None  # No errors, file is valid
    except Exception as e:
        return f"Error processing file: {e}"
