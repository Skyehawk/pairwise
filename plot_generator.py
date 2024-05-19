from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import numpy as np
#import json

#TODO: actually put in processed data in main
#TODO: Weekly stats as well



def generate_plot(processed_files, entry_counts):
    moving_avg_window = 7

    # Convert data to datetime objects and sort by date for processed files
    processed_dates = [datetime.strptime(date, "%Y-%m-%d").date() for date in processed_files.keys()]
    processed_counts = list(processed_files.values())
    processed_data = dict(sorted(zip(processed_dates, processed_counts)))

    # Convert data to datetime objects and sort by date for entry counts
    entry_dates = [datetime.strptime(date, "%Y-%m-%d").date() for date in entry_counts.keys()]
    entry_counts = list(entry_counts.values())
    entry_data = dict(sorted(zip(entry_dates, entry_counts)))

    # Determine the valid date range for the last 60 days or until the first entry
    today = datetime.now().date()
    min_date = min(today - timedelta(days=60), min(processed_data.keys()), min(entry_data.keys()))

    # Filter processed data within the valid date range
    filtered_processed_data = {date: processed_data[date] for date in processed_data if min_date <= date <= today}

    # Filter entry data within the valid date range
    filtered_entry_data = {date: entry_data[date] for date in entry_data if min_date <= date <= today}

    # Fill missing dates within the valid range with zero counts for processed data
    missing_processed_dates = [min_date + timedelta(days=i) for i in range((today - min_date).days + 1) if
                               (min_date + timedelta(days=i)) not in filtered_processed_data]
    for date in missing_processed_dates:
        filtered_processed_data[date] = 0

    # Fill missing dates within the valid range with zero counts for entry data
    missing_entry_dates = [min_date + timedelta(days=i) for i in range((today - min_date).days + 1) if
                           (min_date + timedelta(days=i)) not in filtered_entry_data]
    for date in missing_entry_dates:
        filtered_entry_data[date] = 0

    # Sort the data after adding missing dates for processed data
    filtered_processed_data = dict(sorted(filtered_processed_data.items()))
    print(filtered_processed_data)

    # Sort the data after adding missing dates for entry data
    filtered_entry_data = dict(sorted(filtered_entry_data.items()))
    print(filtered_entry_data)

    # Prepare data for plotting for processed data
    processed_dates = list(filtered_processed_data.keys())
    processed_counts = list(filtered_processed_data.values())

    # Prepare data for plotting for entry data
    entry_dates = list(filtered_entry_data.keys())
    entry_counts = list(filtered_entry_data.values())

    # File trace calculation
    # Calculate n-day moving average for processed data
    processed_smoothed_counts = [sum(processed_counts[i:i + moving_avg_window]) / min(moving_avg_window,
                                                                                     len(processed_counts) - i) for i in
                                 range(len(processed_counts))]

    processed_counts_iqr = np.zeros(len(processed_counts))
    for i in range(len(processed_counts)):
        start = max(0, i - moving_avg_window + 1)
        end = min(len(processed_counts), i + 1)
        processed_counts_iqr[i] = np.percentile(processed_counts[start:end], 75) - np.percentile(processed_counts[start:end], 25)

    # Entries trace calculation
    # Calculate n-day moving average for entry data
    entry_smoothed_counts = [sum(entry_counts[i:i + moving_avg_window]) / min(moving_avg_window,
                                                                             len(entry_counts) - i) for i in
                             range(len(entry_counts))]

    entry_counts_iqr = np.zeros(len(entry_counts))
    for i in range(len(entry_counts)):
        start = max(0, i - moving_avg_window + 1)
        end = min(len(entry_counts), i + 1)
        entry_counts_iqr[i] = np.percentile(entry_counts[start:end], 75) - np.percentile(entry_counts[start:end], 25)


    # Plotting
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

        # Determine Mondays within the date range
    mondays = [date for date in entry_dates if date.weekday() == 0]

    # Iterate through Mondays to plot vertical lines
    for i, monday in enumerate(mondays):
        color='lightgray' #color = 'lightgray' if i % 2 == 0 else 'gray'
        ax1.axvline(x=monday, color=color)
        ax2.axvline(x=monday, color=color)

    # Set x-axis ticks and labels to Mondays
    plt.xticks(mondays, [date.strftime('%Y-%m-%d') for date in mondays], rotation=45, ha='right')

    # Processed data plot
    ax1.plot(processed_dates,
             processed_counts,
             label='Processed Daily (UTC)'
             )

    ax1.plot(processed_dates[1:-1],
             processed_smoothed_counts[1:-1],
             color='orange',
             label=f'Processed {moving_avg_window}-Day Average'
             )

    ax1.fill_between(processed_dates[1:-1],
                     processed_smoothed_counts[1:-1] - processed_counts_iqr[1:-1],
                     processed_smoothed_counts[1:-1] + processed_counts_iqr[1:-1],
                     #vmin=0,
                     color='orange',
                     alpha=0.3,
                     label=f'Processed Files IQR ({moving_avg_window}-Day)'
                     )

    # Entry data plot
    ax2.plot(entry_dates,
             entry_counts,
             label='Entry Comparisons Daily (UTC)'
             )

    ax2.plot(entry_dates[1:-1],
             entry_smoothed_counts[1:-1],
             color='orange',
             label=f'Entry Comparisons {moving_avg_window}-Day Average'
             )

    ax2.fill_between(entry_dates[1:-1],
                 entry_smoothed_counts[1:-1] - entry_counts_iqr[1:-1],
                 entry_smoothed_counts[1:-1] + entry_counts_iqr[1:-1],
                 #vmin=0,
                 color='orange',
                 alpha=0.3,
                 label=f'Entry Comparisons IQR ({moving_avg_window}-Day)'
                 )

    ax1.legend()
    ax2.legend()

    ax1.set_ylabel('Files Processed')
    ax2.set_ylabel('Pairwise Entries Processed')

    # set extent of plots because vmin odesnt work with fill_between apperently
    ax1.set_ylim(0, max(processed_counts) + max(processed_counts_iqr[1:-1]))
    ax2.set_ylim(0, max(entry_counts) + max(entry_counts_iqr[1:-1]))

    plt.xlabel('Date')
    plt.suptitle('Files and Total Pairwise Entries Processed per Day')

    # Convert plot to base64 encoded URL
    img = BytesIO()
    plt.tight_layout()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return plot_url
