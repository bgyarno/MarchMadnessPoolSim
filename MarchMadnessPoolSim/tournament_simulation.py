from MarchMadnessPoolSim import bracket
from MarchMadnessPoolSim import teams
from MarchMadnessPoolSim import game_simulation

bracket_dict = bracket.Bracket()
bracket_dict = bracket_dict.initialize_bracket()
# print(bracket_dict)

def update_successor_game(bracket_dict, region_id, successor_game_id, team_num):
    team1 = sim_results.team1
    team1_seed = game['team1']['seed']
    team2 = sim_results.team2
    team2_seed = game['team2']['seed']
    winning_team = sim_results.winning_team()
    winning_team_index = winning_team.team_index
    if team1.team_index == winning_team_index:
        winning_team_seed = team1_seed
    if team2.team_index == winning_team_index:
        winning_team_seed = team2_seed

    bracket.add_teams(bracket_dict, winning_team.team_name(), winning_team_seed, region_id, successor_game_id, team_num)


def add_game_results(bracket_dict,sim_results, region, game_id):
    region_index = bracket.get_region_index(bracket_dict, region['id'])
    game_id_index = bracket.get_game_id_index(bracket_dict, region['id'], game_id)
    team1 = sim_results.team1
    team1_seed = game['team1']['seed']
    team2 = sim_results.team2
    team2_seed = game['team2']['seed']
    winning_team = sim_results.winning_team()
    winning_team_index = winning_team.team_index
    losing_team = sim_results.losing_team()
    losing_team_index = losing_team.team_index
    win_margin = sim_results.score_delta()

    if team1.team_index == winning_team_index:
        winning_team_seed = team1_seed
    if team2.team_index == winning_team_index:
        winning_team_seed = team2_seed
    results = {'winning_team_name' : winning_team.team_name(),
               'winning_team_index' : winning_team_index,
               'losing_team_name' : losing_team.team_name(),
               'losing_team_index' : losing_team_index,
               'win_margin' : win_margin,
               'winning_team_seed' : winning_team_seed
               }
    bracket_dict['regions'][region_index]['games'][game_id_index]['results'] = results


team_dict = teams.generate_team_dict()
# print(team_dict)
## sim regions
for region in bracket_dict['regions'][0:3]:
    region_id = region['id']
    ## sim first four
    for game in region['games']:
        if game['round']['name'] == 'First Four':
            print(game)
            team1 = teams.Team(team_dict, game['team1']['team_index'])
            team2 = teams.Team(team_dict, game['team2']['team_index'])
            sim_results = game_simulation.GameSim(team1, team2)
            successor_game_id = game['successor']['game_id']
            game_id = game['game_id']
            update_successor_game(bracket_dict, region_id, successor_game_id, 'team2')
            # print([region['games'][i] for i in range(len(region['games'])) if region['games'][i]['game_id'] == successor_game_id])
            add_game_results(bracket_dict, sim_results, region, game_id)
            # print(game)
    ## sim round of 64
    for game in region['games']:
        if game['round']['name'] == 'Round of 64':
            print('Simulating ' + game['round']['name'])
            print(game)
            team1 = teams.Team(team_dict, game['team1']['team_index'])
            team2 = teams.Team(team_dict, game['team2']['team_index'])
            sim_results = game_simulation.GameSim(team1, team2)
            successor_game_id = game['successor']['game_id']
            game_id = game['game_id']
            update_successor_game(bracket_dict, region_id, successor_game_id, 'TBD')
            # print([region['games'][i] for i in range(len(region['games'])) if region['games'][i]['game_id'] == successor_game_id])
            add_game_results(bracket_dict, sim_results, region, game_id)
            # print(game)

    ## sim round of 32
    for game in region['games']:
        if game['round']['name'] == 'Round of 32':
            print('Simulating ' + game['round']['name'])
            print(game)
            team1 = teams.Team(team_dict, game['team1']['team_index'])
            team2 = teams.Team(team_dict, game['team2']['team_index'])
            sim_results = game_simulation.GameSim(team1, team2)
            successor_game_id = game['successor']['game_id']
            game_id = game['game_id']
            update_successor_game(bracket_dict, region_id, successor_game_id, 'TBD')
            # print([region['games'][i] for i in range(len(region['games'])) if region['games'][i]['game_id']['team1'] == successor_game_id])
            add_game_results(bracket_dict, sim_results, region, game_id)
            # print(game)

    ## sim Sweet 16
    for game in region['games']:
        if game['round']['name'] == 'Sweet 16':
            team1 = teams.Team(team_dict, game['team1']['team_index'])
            team2 = teams.Team(team_dict, game['team2']['team_index'])
            sim_results = game_simulation.GameSim(team1, team2)
            successor_game_id = game['successor']['game_id']
            game_id = game['game_id']
            update_successor_game(bracket_dict, region_id, successor_game_id, 'TBD')
            # print([region['games'][i] for i in range(len(region['games'])) if region['games'][i]['game_id'] == successor_game_id])
            add_game_results(bracket_dict, sim_results, region, game_id)
            # print(game)


    ## sim Elite 8
    for game in region['games']:
        if game['round']['name'] == 'Elite 8':
            team1 = teams.Team(team_dict, game['team1']['team_index'])
            team2 = teams.Team(team_dict, game['team2']['team_index'])
            sim_results = game_simulation.GameSim(team1, team2)
            successor_game_id = game['successor']['game_id']
            game_id = game['game_id']
            update_successor_game(bracket_dict, region_id, successor_game_id, 'TBD')
            print([region['games'][i] for i in range(len(region['games'])) if region['games'][i]['game_id'] == successor_game_id])
            add_game_results(bracket_dict, sim_results, region, game_id)
            print(game)

## sim final 4 and championship
for region in bracket_dict['regions'][-1]:
    region_id = region['id']
    ## Final 4
    for game in region['games']:
        if game['round']['name'] == 'Final 4':
            team1 = teams.Team(team_dict, game['team1']['team_index'])
            team2 = teams.Team(team_dict, game['team2']['team_index'])
            sim_results = game_simulation.GameSim(team1, team2)
            successor_game_id = game['successor']['game_id']
            game_id = game['game_id']
            update_successor_game(bracket_dict, region_id, successor_game_id, 'TBD')
            print([region['games'][i] for i in range(len(region['games'])) if
                   region['games'][i]['game_id'] == successor_game_id])
            add_game_results(bracket_dict, sim_results, region, game_id)
            print(game)
    ## sim Final
    for game in region['games']:
        if game['round']['name'] == 'Championship':
            team1 = teams.Team(team_dict, game['team1']['team_index'])
            team2 = teams.Team(team_dict, game['team2']['team_index'])
            sim_results = game_simulation.GameSim(team1, team2)
            successor_game_id = game['successor']['game_id']
            game_id = game['game_id']
            print([region['games'][i] for i in range(len(region['games'])) if
                   region['games'][i]['game_id'] == successor_game_id])
            add_game_results(bracket_dict, sim_results, region, game_id)
            print(game)
