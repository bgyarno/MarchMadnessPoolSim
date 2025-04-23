from MarchMadnessPoolSim import bracket
from MarchMadnessPoolSim import teams
from MarchMadnessPoolSim import game_simulation
import sys


def update_successor_game(bracket_dict, region_id, game, successor_game_id, team_num, sim_results):
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


def add_game_results(bracket_dict, sim_results, region, game_id, game):
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
    results = {'winning_team_name': winning_team.team_name(),
               'winning_team_index': winning_team_index,
               'losing_team_name': losing_team.team_name(),
               'losing_team_index': losing_team_index,
               'win_margin': win_margin,
               'winning_team_seed': winning_team_seed
               }
    bracket_dict['regions'][region_index]['games'][game_id_index]['results'] = results


def simulate_region_round(bracket_dict, team_dict, region, round_name, update_successors=True):
    for game in region['games']:
        if game['round']['name'] == round_name:
            # print('Simulating Region #' + str(region['id']) + ' ' + game['round']['name'])
            region_id = region['id']
            team1 = teams.Team(team_dict, game['team1']['team_index'])
            team2 = teams.Team(team_dict, game['team2']['team_index'])
            sim_results = game_simulation.GameSim(team1, team2)
            game_id = game['game_id']
            if update_successors:
                successor_game_id = game['successor']['game_id']
                if round_name == 'First Four':
                    update_successor_game(bracket_dict, region_id, game, successor_game_id, 'team2', sim_results)
                elif round_name == 'Elite 8':
                    update_successor_game(bracket_dict, 5, game, successor_game_id, 'TBD', sim_results)
                else:
                    update_successor_game(bracket_dict, region_id, game, successor_game_id, 'TBD', sim_results)

            add_game_results(bracket_dict, sim_results, region, game_id, game)


def sim_tourney(team_dict, bracket_dict):
    ## sim regions
    for region in bracket_dict['regions'][0:4]:
        ## sim first four
        simulate_region_round(bracket_dict, team_dict, region, round_name='First Four', update_successors=True)

        ## sim round of 64
        simulate_region_round(bracket_dict, team_dict, region, round_name='Round of 64', update_successors=True)

        ## sim round of 32
        simulate_region_round(bracket_dict, team_dict, region, round_name='Round of 32', update_successors=True)

        ## sim Sweet 16
        simulate_region_round(bracket_dict, team_dict, region, round_name='Sweet 16', update_successors=True)

        ## sim Elite 8
        simulate_region_round(bracket_dict, team_dict, region, round_name='Elite 8', update_successors=True)

    ## sim final 4 and championship
    region = bracket_dict['regions'][-1]
    simulate_region_round(bracket_dict, team_dict, region, round_name='Final 4', update_successors=True)
    simulate_region_round(bracket_dict, team_dict, region, round_name='Championship Game', update_successors=False)

    return (bracket_dict)


class TournamentSimIteration:
    def __init__(self, team_dict, bracket_dict):
        self.team_dict = team_dict
        self.bracket_dict = bracket_dict
        self.sim_results = sim_tourney(self.team_dict, self.bracket_dict)

    def biggest_blowout_game(self):
        max_value = 0
        for region in self.sim_results['regions']:
            for game in region['games']:
                value = game['results']['win_margin']
                if value > max_value:
                    max_value = value
                    max_game = game
        return (max_game)

    def biggest_blowout_team_name(self):
        team = self.biggest_blowout_game()['results']['losing_team_name']
        return (team)

    def biggest_blowout_team_index(self):
        team = self.biggest_blowout_game()['results']['losing_team_index']
        return (team)

    def biggest_blowout_margin(self):
        margin = self.biggest_blowout_game()['results']['win_margin']
        return (margin)

    def team_results(self):
        dict = {}
        for region in self.sim_results['regions']:
            ## append team 1 results
            for game in region['games']:
                team_index = game['team1']['team_index']
                team_name = game['team1']['name']
                win_margin = game['results']['win_margin']
                if game['results']['winning_team_index'] == team_index:
                    win = True
                    biggest_blowout_loss = False
                    margin = win_margin
                if game['results']['losing_team_index'] == team_index:
                    win = False
                    margin = -win_margin
                    if game['game_id'] == self.biggest_blowout_game()['game_id']:
                        biggest_blowout_loss = True
                    else:
                        biggest_blowout_loss = False
                result_summary = {'game_id': game['game_id'],
                                  'round': game['round']['name'],
                                  'seed': game['team1']['seed'],
                                  'win': win,
                                  'margin': margin,
                                  'biggest_blowout_loss': biggest_blowout_loss
                                  }
                if team_index not in dict.keys():
                    dict[team_index] = {'team_name': team_name,
                                        'games': [result_summary]
                                        }
                else:
                    dict[team_index]['games'].append(result_summary)
            ## append team 2 results
            for game in region['games']:
                team_index = game['team2']['team_index']
                team_name = game['team2']['name']
                win_margin = game['results']['win_margin']
                if game['results']['winning_team_index'] == team_index:
                    win = True
                    biggest_blowout_loss = False
                    margin = win_margin
                if game['results']['losing_team_index'] == team_index:
                    win = False
                    margin = -win_margin
                    if game['game_id'] == self.biggest_blowout_game()['game_id']:
                        biggest_blowout_loss = True
                    else:
                        biggest_blowout_loss = False
                result_summary = {'game_id': game['game_id'],
                                  'round': game['round']['name'],
                                  'seed': game['team2']['seed'],
                                  'win': win,
                                  'margin': margin,
                                  'biggest_blowout_loss': biggest_blowout_loss
                                  }
                if team_index not in dict.keys():
                    dict[team_index] = {'team_name': team_name,
                                        'games': [result_summary]
                                        }
                else:
                    dict[team_index]['games'].append(result_summary)
        return (dict)

    def team_result_summary(self):
        results = self.team_results()
        dict = {}
        for key, value in results.items():
            wins = sum([game['win'] for game in value['games'] if game['round'] != 'First Four'])
            seed = max([game['seed'] for game in value['games']])
            round_64_win = 1 if [game['win'] for game in value['games'] if
                                 game['round'] == 'Round of 64' and game['win']] else 0
            round_32_win = 1 if [game['win'] for game in value['games'] if
                                 game['round'] == 'Round of 32' and game['win']] else 0
            sweet_16_win = 1 if [game['win'] for game in value['games'] if
                                 game['round'] == 'Sweet 16' and game['win']] else 0
            elite_8_win = 1 if [game['win'] for game in value['games'] if
                                game['round'] == 'Elite 8' and game['win']] else 0
            final_4_win = 1 if [game['win'] for game in value['games'] if
                                game['round'] == 'Final 4' and game['win']] else 0
            final_win = 1 if [game['win'] for game in value['games'] if
                              game['round'] == 'Championship Game' and game['win']] else 0
            biggest_blowout_loss = max([game['biggest_blowout_loss'] for game in value['games']])
            biggest_blowout_margin = min(game['margin'] if game['margin'] == True else 0 for game in value['games'])
            dict[key] = {'team_name': value['team_name'],
                         'wins': wins,
                         'round_64_win': round_64_win,
                         'round_32_win': round_32_win,
                         'sweet_16_win': sweet_16_win,
                         'elite_8_win': elite_8_win,
                         'final_4_win': final_4_win,
                         'final_win': final_win,
                         'biggest_blowout_loss': biggest_blowout_loss,
                         'biggest_blowout_margin': biggest_blowout_margin,
                         'seed': seed}
        return (dict)


class TournamentSim:
    def __init__(self, team_dict, bracket_dict, iterations):
        self.team_dict = team_dict
        self.bracket_dict = bracket_dict
        self.iterations = iterations
        self.iteration_results = self.iteration_results()

    def iteration_results(self):
        i = 0
        iteration_dict = {}
        print('Simulating ' + str(self.iterations) + ' Tournaments')
        while i < self.iterations:
            n = i+1
            j = self.iterations / 50
            k = round(n / j)
            sys.stdout.write('\r')
            sys.stdout.write("[%-50s] %d of %i" % ('='*k, n, self.iterations))
            sys.stdout.flush()
            result = TournamentSimIteration(self.team_dict, self.bracket_dict)
            iteration_dict[i] = result.team_result_summary()
            i += 1
        return (iteration_dict)

    def team_summary(self):
        summary_dict = {}
        ## create dictionary of teams and result values
        for iter_key, iter_value in self.iteration_results.items():
            for key, value in iter_value.items():
                if key not in summary_dict.keys():
                    summary_dict[key] = {'team_name': value['team_name'],
                                         'seed': value['seed'],
                                         'win_results': [value['wins']],
                                         'biggest_blowout_loss_results': [value['biggest_blowout_loss']],
                                         'round_64_win_results': [value['round_64_win']],
                                         'round_32_win_results': [value['round_32_win']],
                                         'sweet_16_win_results': [value['sweet_16_win']],
                                         'elite_8_win_results': [value['elite_8_win']],
                                         'final_4_win_results': [value['final_4_win']],
                                         'final_win_results': [value['final_win']],

                                         }
                else:
                    summary_dict[key]['win_results'].append(value['wins'])
                    summary_dict[key]['biggest_blowout_loss_results'].append(value['biggest_blowout_loss'])
                    summary_dict[key]['round_64_win_results'].append(value['round_64_win'])
                    summary_dict[key]['round_32_win_results'].append(value['round_32_win'])
                    summary_dict[key]['sweet_16_win_results'].append(value['sweet_16_win'])
                    summary_dict[key]['elite_8_win_results'].append(value['elite_8_win'])
                    summary_dict[key]['final_4_win_results'].append(value['final_4_win'])
                    summary_dict[key]['final_win_results'].append(value['final_win'])
        ## summarize result values
        for key, value in summary_dict.items():
            summary_dict[key]['avg_wins'] = sum(summary_dict[key]['win_results']) / len(
                summary_dict[key]['win_results'])
            summary_dict[key]['biggest_blowout_pct'] = sum(summary_dict[key]['biggest_blowout_loss_results']) / len(
                summary_dict[key]['biggest_blowout_loss_results'])
            summary_dict[key]['round_64_win_pct'] = sum(summary_dict[key]['round_64_win_results']) / len(
                summary_dict[key]['round_64_win_results'])
            summary_dict[key]['round_32_win_pct'] = sum(summary_dict[key]['round_32_win_results']) / len(
                summary_dict[key]['round_32_win_results'])
            summary_dict[key]['sweet_16_win_pct'] = sum(summary_dict[key]['sweet_16_win_results']) / len(
                summary_dict[key]['sweet_16_win_results'])
            summary_dict[key]['elite_8_win_pct'] = sum(summary_dict[key]['elite_8_win_results']) / len(
                summary_dict[key]['elite_8_win_results'])
            summary_dict[key]['final_4_win_pct'] = sum(summary_dict[key]['final_4_win_results']) / len(
                summary_dict[key]['final_4_win_results'])
            summary_dict[key]['final_win_pct'] = sum(summary_dict[key]['final_win_results']) / len(
                summary_dict[key]['final_win_results'])
            summary_dict[key].pop('win_results')
            summary_dict[key].pop('biggest_blowout_loss_results')
            summary_dict[key].pop('round_64_win_results')
            summary_dict[key].pop('round_32_win_results')
            summary_dict[key].pop('sweet_16_win_results')
            summary_dict[key].pop('elite_8_win_results')
            summary_dict[key].pop('final_4_win_results')
            summary_dict[key].pop('final_win_results')

        return (summary_dict)

    def round_summary(self):
        team_summary = self.team_summary()
        round_dict = {}
        for key, value in team_summary.items():
            for round in ['round_64', 'round_32', 'sweet_16', 'elite_8', 'final_4', 'final']:
                round_value = round + '_win_pct'
                team_round_value = {key: value[round_value]}
                if round not in round_dict.keys():
                    round_dict[round] = [team_round_value]
                else:
                    round_dict[round].append(team_round_value)
        return(round_dict)

