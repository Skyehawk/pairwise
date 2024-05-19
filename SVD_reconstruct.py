from flask import Flask, make_response, request, render_template, jsonify

from processing import process_data
from validation import validate_file
from plot_generator import generate_plot
from entry_counter_updater import update_entry_counts, get_entry_counts

from werkzeug.utils import secure_filename
import os
import csv
from datetime import datetime, date
import json
import html
import fcntl  # File locking

#from tbapy import TBA as tba

#import sys
#sys.path.append('./templates/TBA_scripts/')
from get_teams_from_event_match import get_teams

app = Flask(__name__)
app.config["DEBUG"] = True
app.config["SECRET_KEY"] = "lkmasafeacadfghjgppzhbvgfkhtq"


# File to store the counter
#FILE_COUNTER = "Pairwise_reconstruction/file_counter.txt"
FILE_PROCESSED_BY_DATE = "Pairwise_reconstruction/processed_files_by_date.json"
FILE_ENTRIES_BY_DATE = "Pairwise_reconstruction/entry_counter.json"
LOCK_FILE = "Pairwise_reconstruction/lock_file.lock"

# Functions for file locking
def acquire_lock():
    lock_file = open(LOCK_FILE, 'w')
    fcntl.flock(lock_file, fcntl.LOCK_EX)
    return lock_file

def release_lock(lock_file):
    fcntl.flock(lock_file, fcntl.LOCK_UN)
    lock_file.close()

#functions for managing file processed counts
def get_processed_files_by_date():
    try:
        with open(FILE_PROCESSED_BY_DATE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_processed_files_by_date(processed_files):
    with open(FILE_PROCESSED_BY_DATE, "w") as file:
        json.dump(processed_files, file)

def get_processed_files_count():
    try:
        lock_file = acquire_lock()
        try:
            with open(FILE_PROCESSED_BY_DATE, "r") as file:
                processed_files = json.load(file)
                total_files_processed = sum(processed_files.values())
                return total_files_processed
        finally:
            release_lock(lock_file)
    except FileNotFoundError:
        return 0


#functions for saving user submitted file if they choose to
def save_user_submitted_file(file, memo=""):
    user_submitted_dir = "Pairwise_reconstruction/user_submitted_files"
    if not os.path.exists(user_submitted_dir):
        os.makedirs(user_submitted_dir)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = secure_filename(file.filename)
    file_extension = os.path.splitext(filename)[1]
    new_filename = f"{timestamp}_{filename}{file_extension}"

    # Reset file cursor before reading the content
    file.seek(0)
    submitted_file_content = file.stream.read().decode("utf-8")
    with open(os.path.join(user_submitted_dir, f"{timestamp}_{filename}.txt"), "w") as content_file:
        content_file.write(submitted_file_content)

    # Print content for verification
    print(f"Content of {new_filename}: {submitted_file_content}")

    # Update the submitted_file_index.csv
    index_file = os.path.join(user_submitted_dir, "submitted_file_index.csv")
    with open(index_file, "a", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([timestamp, f"{timestamp}_{filename}.txt", memo])

@app.route('/')
def index():
    lock_file = acquire_lock()
    try:
        processed_files = get_processed_files_by_date()
        total_files_processed = sum(processed_files.values())
    finally:
        release_lock(lock_file)
    return render_template('index.html', total_files_processed=total_files_processed)

@app.route('/datagen')
def datagen():
    return render_template('datagen.html')

@app.route('/testing')
def testing():
    return render_template('testing.html')

@app.route('/datagen_exp')
def datagen_exp():
    return render_template('datagen_experimental.html')

@app.route('/get_teams', methods=['POST'])
def fetch_teams():
    data = request.get_json()
    event_code = data.get('event_code')
    match_number = data.get('match_number')

    if event_code and match_number:
        teams = get_teams(event_code, match_number)
        return jsonify(teams)
    else:
        return jsonify({'error': 'Invalid data format or missing parameters.'})

@app.route('/stats')
def stats():
    lock_file = acquire_lock()
    try:
        processed_files = get_processed_files_by_date()
        total_files_processed = sum(processed_files.values())

        entry_counts = get_entry_counts(FILE_ENTRIES_BY_DATE)['total_entries']
        #print("entry_counts", entry_counts)
    finally:
        release_lock(lock_file)
    plot_url = generate_plot(processed_files, entry_counts)
    return render_template('stats.html', total_files_processed=total_files_processed, entry_counts=entry_counts,  plot_url=plot_url)


@app.route("/file-processing", methods=["GET", "POST"])
def file_processing():
    if request.method == "POST":
        lock_file = acquire_lock()
        #processed_files = get_processed_files_by_date()
        #total_files_processed = 0#sum(processed_files.values()) # var needs to exist at this scope for render template

        input_file = request.files["input_file"]
        from_match_value = int(request.form.get('fromInputValueForm'))
        to_match_value = int(request.form.get('toInputValueForm'))
        exclude_flag_1 = request.form.get('excludeFlag1Form')

        if exclude_flag_1 == 'true':
            exclude_flag_1 = True
        elif exclude_flag_1 =='false':
            exclude_flag_1 = False

        # Check if a file was uploaded
        if input_file.filename == "":
            return "No file selected."

        # Check the file extension
        if not input_file.filename.lower().endswith(('.csv', '.txt')):
            return "Please upload a .csv or .txt file."

        try:
            # Read the contents of the file
            contents = input_file.stream.read().decode("utf-8")

            # Perform validation using the separate file
            validation_result = validate_file(contents)
            if validation_result:
                return validation_result

            # Process the input data

            output_data = process_data(contents, from_match_value, to_match_value, exclude_flag_1)

            # Update processed files by date
            today = str(date.today())
            processed_files = get_processed_files_by_date()
            processed_files[today] = processed_files.get(today, 0) + 1
            save_processed_files_by_date(processed_files)

            # Read (updated) processed files by date for counter
            # processed_files = get_processed_files_by_date()
            # total_files_processed = sum(processed_files.values())

            # Count number of lines in the input file
            line_count = contents.count('\n') + 1  # Count newline characters to get the line count
            # Update date_count_data with the line count for the current date
            date_count_data = {} # can take a multi key dict, but will normally send this form: date_count_data = {"2023-12-01": 150}
            date_count_data[today] = line_count
            update_entry_counts(FILE_ENTRIES_BY_DATE, date_count_data)

            # Return a response or redirect as needed
            # return "File processed successfully!"
        except Exception as e:
            return f"Error processing file: {e}"
        finally:
            release_lock(lock_file)

        memo = request.form.get("memo")

        # Sanitize memo text on the server-side
        sanitized_memo = html.escape(memo) if memo else ""

        if request.form.get("submitData") == "on":
            save_user_submitted_file(input_file, sanitized_memo)

        # Create a response with the processed data
        response = make_response(output_data)
        response.headers["Content-Disposition"] = "attachment; filename=result.csv"
        return response

    # If the request method is GET, display the file upload form
    return render_template('file_processing.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/change-log')
def changelog():
    return render_template('changelog.html')

@app.route('/help-SVD')
def help_SVD():
    return render_template('help-SVD.html')

@app.route('/help-datagen')
def help_datagen():
    return render_template('help-datagen.html')

@app.route('/help-overview')
def help_overview():
    return render_template('help-overview.html')

@app.route('/help-basic-tutorial')
def help_basic_tutorial():
    return render_template('help-basic-tutorial.html')


if __name__ == "__main__":
    app.run()
