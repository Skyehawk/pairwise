import os
from datetime import datetime
import csv

def save_user_submitted_file(file, memo=""):
    # Create a directory to store user-submitted files if it doesn't exist
    user_submitted_dir = "user_submitted_files"
    if not os.path.exists(user_submitted_dir):
        os.makedirs(user_submitted_dir)

    # Get current date and time
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Get filename and extension
    filename = secure_filename(file.filename)
    file_extension = os.path.splitext(filename)[1]

    # Generate a new filename with timestamp
    new_filename = f"{timestamp}_{filename}{file_extension}"

    # Save the file in the user_submitted_files directory
    file.save(os.path.join(user_submitted_dir, new_filename))

    # Create or append to the submitted_file_index.csv
    index_file = os.path.join(user_submitted_dir, "submitted_file_index.csv")
    with open(index_file, "a", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([timestamp, new_filename, str(memo)])

# Example usage:
# Assuming 'submitted_file' is the uploaded file and 'memo_text' is the submitted memo
submitted_file = # The uploaded file object
memo_text = # The submitted memo text

# Call the function to save the user-submitted file and update the index
save_user_submitted_file(submitted_file, memo_text)
