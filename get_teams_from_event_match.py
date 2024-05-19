from tbapy import TBA

def get_teams(event_code, match_number):
    # Replace 'YOUR_API_KEY_HERE' with your actual TBA API key
    tba = TBA('wJchZmpG4UDto4tAm6eEWkaIXYpfzA3BWSdfUG2qjJO5MD8AoRTR9rbOIgC9J2yQ')

    match = tba.match(f"{event_code}_qm{match_number}", simple=True)
    print(match)

    if match:
        red_teams = match['alliances']['red']['team_keys']
        blue_teams = match['alliances']['blue']['team_keys']

        # Extracting team numbers from the keys
        red_team_numbers = [team[3:] for team in red_teams]
        blue_team_numbers = [team[3:] for team in blue_teams]

        teams_dict = {
            'red_teams': red_team_numbers,
            'blue_teams': blue_team_numbers
        }

        return teams_dict
    else:
        return None