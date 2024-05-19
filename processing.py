#'''https://www.sciencedirect.com/science/article/abs/pii/S1063520321000233?fr=RR-2&ref=pdf_download&rr=7dd847563a9e114b'''
import numpy as np
from scipy.linalg import svd, LinAlgError
#import csv
from io import StringIO
import pandas as pd

def pairwise_ranking_recovery(comparisons):
    # Extract unique items from comparisons
    items = set([item for pair in comparisons for item in pair[:2]])
    num_items = len(items)

    # Create a mapping of items to indices
    item_indices = {item: i for i, item in enumerate(items)}

    # Create an empty matrix to store the pairwise comparisons
    matrix = np.zeros((num_items, num_items))

    # Populate the matrix with pairwise comparison values
    for a, b, x in comparisons:
        i = item_indices[a]
        j = item_indices[b]
        matrix[i, j] = x

    # Perform low-rank matrix completion using Singular Value Decomposition (SVD)
    U = None
    S = None
    Vt = None
    try:
      U, S, Vt = svd(matrix)
    except LinAlgError as e:
      print(f'an error occured: {e} - Likely the SVD computation did not converge.')
      return {},{}

    # Estimate the completed matrix by reconstructing with a reduced rank
    rank = min(num_items, len(comparisons))
    S_hat = np.diag(S[:rank])
    completed_matrix = U[:, :rank] @ S_hat @ Vt[:rank, :]

    # Calculate the average ranking for each item
    item_ranks = np.mean(completed_matrix, axis=1)

    # Create a ranking dictionary for each item
    ranking_dict = {item: rank for item, rank in zip(items, item_ranks)}

    # Sort the items based on their ranking
    sorted_ranking = sorted(ranking_dict.items(), key=lambda x: x[1], reverse=True)

    # Calculate the improvement of each item's ranking over the average
    avg_rank = np.mean(item_ranks)
    improvement_dict = {item: round(avg_rank - rank, 3) for item, rank in sorted_ranking}

    return sorted_ranking, improvement_dict

def normalize_tuples(lst):
    normalized_list = []
    max_value = max(float(t[2]) for t in lst)
    min_value = min(float(t[2]) for t in lst)

    for t in lst:
        normalized_value = 3 * (float(t[2]) - min_value) / (max_value - min_value)
        normalized_tuple = (str(t[0]), str(t[1]), float(normalized_value))
        normalized_list.append(normalized_tuple)

    return normalized_list


def process_data(input_data, min_match=1, max_match=1000, exclude_flag_1=False):
    # Split the string by lines and then by commas to create a list of lists
    print('--------- new processing ---------')
    lines = input_data.split('\n')
    csv_data = [line.split(',') for line in lines]
    csv_data = [tuple(item.strip('\r') for item in row) for row in csv_data]

    # Initialize an empty list to store the tuples
    pairwise_observations = []

    # Iterate through each row in the CSV data
    for row in csv_data:
    # Check if the row has at least three elements before accessing them
        if len(row) >= 3:
            team1, team2, diff = row[0], row[1], row[2]

            match_number = None
            flag_1 = 0  #robot was incapacitated (1), working normally(0)
            if  len(row) >= 4:
                if str(row[3]).lstrip().isdigit():
                    match_number = int(str(row[3]).lstrip())
            if  len(row) >= 5 and exclude_flag_1:
                if str(row[4]).lstrip().isdigit():
                    flag_1 = int(str(row[4]).lstrip())
                    print(f'flag_1: {flag_1}')



            exclude_match = False

            if (int(match_number) < int(min_match)) or (int(match_number) > int(max_match)):
                 exclude_match = True

            if (exclude_flag_1 == True) and (flag_1 != 0):
                exclude_match = True



            # If match_number is None, still include the teams and differences
            value1, value2, value3 = str(team1), str(team2), str(diff)

            # Check if match_number is not None and is within the specified range
            if exclude_match == False:
                    pairwise_observations.append((value1, value2, value3))
                    #print((value1, value2, value3))

    print(f'obs: {pairwise_observations}')
    print(f'number of observations to compute with: {len(pairwise_observations)}')

    #Calculate
    ranking, improvement = pairwise_ranking_recovery(normalize_tuples(pairwise_observations))

    pd.DataFrame(columns=["rank_score", "rank_mean_departure"])

    # Print the final ranking and improvement for each item
    d={}
    for item, rank in ranking:
        improvement_score = improvement[item]
        d[item] = {'rank_score':round(rank,3), 'rank_mean_departure':improvement_score}
        #print(f"{item}: Rank - {rank:.3f}, Rank improvement over mean- {improvement_score:.3f}")
    result_out_df = pd.DataFrame(d).T

    # Return the result csv string
    csv_out_string = StringIO()
    result_out_df.to_csv(csv_out_string, index=True)  #team numbers are the idx, so we keep it
    csv_out_string.seek(0)
    csv_out_data = csv_out_string.read()
    return(csv_out_data)

