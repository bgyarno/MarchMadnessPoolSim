from MarchMadnessPoolSim import (
    bracket,
    teams,
    game_simulation,
    team_index,
)
import json
import sys
import pandas as pd
import statistics


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

    ## pre-game projections
    team1_spread = sim_results.team1_spread()
    team2_spread = -team1_spread
    total = sim_results.team1_projected_points() + sim_results.team2_projected_points()
    team1_wp = sim_results.team1_win_prob()
    team2_wp = 1.0 - team1_wp

    if team1.team_index == winning_team_index:
        winning_team_seed = team1_seed
    if team2.team_index == winning_team_index:
        winning_team_seed = team2_seed
    results = {'winning_team_name': winning_team.team_name(),
               'winning_team_index': winning_team_index,
               'losing_team_name': losing_team.team_name(),
               'losing_team_index': losing_team_index,
               'win_margin': win_margin,
               'winning_team_seed': winning_team_seed,
               'team1_spread': team1_spread,
               'team2_spread': team2_spread,
               'total': total,
               'team1_wp': team1_wp,
               'team2_wp': team2_wp
               }
    bracket_dict['regions'][region_index]['games'][game_id_index]['results'] = results


def simulate_region_round(bracket_dict, team_dict, region, round_name, source, update_successors=True):
    for game in region['games']:
        if game['round']['name'] == round_name:
            region_id = region['id']
            team1 = teams.Team(team_dict, game['team1']['team_index'])
            team2 = teams.Team(team_dict, game['team2']['team_index'])
            sim_results = game_simulation.GameSim(team1, team2, source)
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


def sim_tourney(team_dict, source, cached_bracket=False, bracket_dir='./bracket.js'):
    if cached_bracket:
        with open(bracket_dir, "r", encoding='utf-8') as f:
            bracket_dict = json.load(f)
    else:
        bracket_dict = bracket.Bracket().initialize_bracket()
    ## sim regions
    for region in bracket_dict['regions'][0:4]:
        ## sim first four
        simulate_region_round(bracket_dict, team_dict, region, round_name='First Four', source=source,
                              update_successors=True)

        ## sim round of 64
        simulate_region_round(bracket_dict, team_dict, region, round_name='Round of 64', source=source,
                              update_successors=True)

        ## sim round of 32
        simulate_region_round(bracket_dict, team_dict, region, round_name='Round of 32', source=source,
                              update_successors=True)

        ## sim Sweet 16
        simulate_region_round(bracket_dict, team_dict, region, round_name='Sweet 16', source=source,
                              update_successors=True)

        ## sim Elite 8
        simulate_region_round(bracket_dict, team_dict, region, round_name='Elite 8', source=source,
                              update_successors=True)

    ## sim final 4 and championship
    region = bracket_dict['regions'][-1]
    simulate_region_round(bracket_dict, team_dict, region, round_name='Final 4', source=source, update_successors=True)
    simulate_region_round(bracket_dict, team_dict, region, round_name='Championship Game', source=source,
                          update_successors=False)
    return (bracket_dict)


class TournamentSimIteration:
    def __init__(self, team_dict, source, bracket_args={}, ):
        self.team_dict = team_dict
        self.bracket_args = bracket_args
        self.source = source
        self.sim_results = sim_tourney(self.team_dict, self.source, **self.bracket_args)

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

    def raw_sim_output(self):
        return self.sim_results

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
    def __init__(self, iterations=100, source='blended', team_dict_args={}, bracket_args={}, cached_result=False,
                 output='sim_results.js'):
        self.cached_result = cached_result
        if self.cached_result:
            self.team_dict_args = {'cached_ratings': True}
        else:
            self.team_dict_args = team_dict_args
        self.team_dict = teams.generate_team_dict(**self.team_dict_args)
        self.bracket_args = bracket_args
        self.iterations = iterations
        self.source = source
        self.output = output
        self.iteration_results = self.iteration_results()

    def iteration_results(self):
        if not self.cached_result:
            i = 0
            iteration_dict = {}
            print('Simulating ' + str(self.iterations) + ' Tournaments')
            while i < self.iterations:
                if i > 0:
                    self.bracket_args = {'cached_bracket': True}
                n = i + 1
                j = self.iterations / 50
                k = round(n / j)
                sys.stdout.write('\r')
                sys.stdout.write("[%-50s] %d of %i" % ('=' * k, n, self.iterations))
                sys.stdout.flush()
                result = TournamentSimIteration(
                    team_dict=self.team_dict,
                    bracket_args=self.bracket_args,
                    source=self.source
                )
                iteration_dict[i] = {}
                iteration_dict[i]['summary'] = result.team_result_summary()
                iteration_dict[i]['results'] = result.raw_sim_output()
                i += 1
            with open(self.output, 'w', encoding='utf-8') as f:
                json.dump(iteration_dict, f)
        else:
            with open(self.output, "r", encoding='utf-8') as f:
                iteration_dict = json.load(f)
        return (iteration_dict)

    def team_summary(self, output_format='json', output_dir='./results_team_summary'):
        summary_dict = {}
        c = pd.read_csv('./auction_order.csv')
        idx = team_index()
        c['index'] = [idx[team] for team in c['Team']]
        ## create dictionary of teams and result values
        for iter_key, iter_value in self.iteration_results.items():
            for key, value in iter_value['summary'].items():
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
        if output_format == 'json':
            with open(output_dir + '.json', 'w', encoding='utf-8') as f:
                json.dump(summary_dict, f)
        if output_format == 'csv':
            df = pd.DataFrame.from_dict(summary_dict, orient='index').reset_index()
            df=df.merge(c[['index', 'Order']], how = 'left', left_on='index', right_on ='index' )
            print(df)
            df.rename(columns={'index': 'team_index'}, inplace=True)
            df.to_csv(output_dir + '.csv', index=False)
        return (summary_dict)

    def pool_value_pick10(self, output_format='json', output_dir='./pool_value_pick10'):
        team_score_dict = {}
        for iter_key, iter_value in self.iteration_results.items():
            for key, value in iter_value['summary'].items():
                r1_score = value['round_64_win'] * int(value['seed'])
                r2_score = value['round_32_win'] * int(value['seed']) * 2
                r3_score = value['sweet_16_win'] * int(value['seed']) * 3
                r4_score = value['elite_8_win'] * int(value['seed']) * 4
                r5_score = value['final_4_win'] * int(value['seed']) * 5
                r6_score = value['final_win'] * int(value['seed']) * 6
                sim_points = r1_score + r2_score + r3_score + r4_score + r5_score + r6_score
                if key not in team_score_dict.keys():
                    team_score_dict[key] = {'team_name': value['team_name'],
                                            'seed': value['seed'],
                                            'sim_point_results': [sim_points]
                                            }
                else:
                    team_score_dict[key]['sim_point_results'].append(sim_points)

        ## summarize results
        for key, value in team_score_dict.items():
            value['mean_points'] = sum(value['sim_point_results']) / len(value['sim_point_results'])
            value['stdev_points'] = statistics.stdev(value['sim_point_results'])
            value.pop('sim_point_results')

        if output_format == 'json':
            with open(output_dir + '.json', 'w', encoding='utf-8') as f:
                json.dump(team_score_dict, f)
        if output_format == 'csv':
            df = pd.DataFrame.from_dict(team_score_dict, orient='index').reset_index()
            df.rename(columns={'index': 'team_index'}, inplace=True)
            df.to_csv(output_dir + '.csv', index=False)

        return team_score_dict

    def bracket_matchups(self, output_dir = './matchups', output_format = 'json'):
        matchup_dict = {'regions': []}
        for iter_key, iter_value in self.iteration_results.items():
            for key, value in iter_value['results'].items():
                for region in value:
                    ## append region ID if they don't exist
                    if region['id'] not in [matchup_dict['regions'][i]['id'] for i in
                                            range(len(matchup_dict['regions']))]:
                        matchup_dict['regions'].append({'id': region['id'], 'rounds': []})
                    region_index = next(
                        (i for i, d in enumerate(matchup_dict['regions']) if d.get('id') == region['id']), -1)

                    ## iterate game results for all simulations, append round, team and opponent info
                    for game in region['games']:
                        ## append round names to regions if they don't exist
                        if game['round']['name'] not in [matchup_dict['regions'][region_index]['rounds'][i]['id'] for i
                                                         in
                                                         range(len(matchup_dict['regions'][region_index]['rounds']))]:
                            matchup_dict['regions'][region_index]['rounds'].append(
                                {'id': game['round']['name'], 'teams': []})
                        round_index = next(
                            (i for i, d in enumerate(matchup_dict['regions'][region_index]['rounds']) if
                             d.get('id') == game['round']['name']), -1)

                        # append team data to list of teams in each region/round for team1
                        if game['team1']['team_index'] not in [
                            matchup_dict['regions'][region_index]['rounds'][round_index]['teams'][i][
                                'team_index'] for i
                            in
                            range(len(matchup_dict['regions'][region_index]['rounds'][round_index]['teams']))]:
                            matchup_dict['regions'][region_index]['rounds'][round_index]['teams'].append(
                                game['team1'].copy())
                        team_index = next(
                            (i for i, d in
                             enumerate(matchup_dict['regions'][region_index]['rounds'][round_index]['teams']) if
                             d.get('team_index') == game['team1']['team_index']), -1)

                        ## add opponents array for team 1 if it doesn't exist
                        try:
                            matchup_dict['regions'][region_index]['rounds'][round_index]['teams'][team_index][
                                'opponents']
                        except KeyError:
                            matchup_dict['regions'][region_index]['rounds'][round_index]['teams'][team_index][
                                'opponents'] = []

                        ## append list of opponents to team1 for each region/round
                        if game['team2']['team_index'] not in [
                            matchup_dict['regions'][region_index]['rounds'][round_index]['teams'][team_index][
                                'opponents'][i]['team_index'] for i
                            in
                            range(len(
                                matchup_dict['regions'][region_index]['rounds'][round_index]['teams'][team_index][
                                    'opponents']))]:
                            matchup_dict['regions'][region_index]['rounds'][round_index]['teams'][team_index][
                                'opponents'].append(
                                {**game['team2'], 'spread': game['results']['team1_spread'],
                                 'total': game['results']['total'],
                                 'win_prob': game['results']['team1_wp']})

                        ## team to region/round list for team 2
                        if game['team2']['team_index'] not in [
                            matchup_dict['regions'][region_index]['rounds'][round_index]['teams'][i]['team_index'] for i
                            in
                            range(len(matchup_dict['regions'][region_index]['rounds'][round_index]['teams']))]:
                            matchup_dict['regions'][region_index]['rounds'][round_index]['teams'].append(
                                game['team2'].copy())

                        team2_index = next(
                            (i for i, d in
                             enumerate(matchup_dict['regions'][region_index]['rounds'][round_index]['teams']) if
                             d.get('team_index') == game['team2']['team_index']), -1)
                        ## add opponents array for team 2
                        try:
                            matchup_dict['regions'][region_index]['rounds'][round_index]['teams'][team2_index][
                                'opponents']
                        except KeyError:
                            matchup_dict['regions'][region_index]['rounds'][round_index]['teams'][team2_index][
                                'opponents'] = []

                        if game['team1']['team_index'] not in [
                            matchup_dict['regions'][region_index]['rounds'][round_index]['teams'][team2_index][
                                'opponents'][i]['team_index'] for i
                            in
                            range(len(
                                matchup_dict['regions'][region_index]['rounds'][round_index]['teams'][team2_index][
                                    'opponents']))]:
                            matchup_dict['regions'][region_index]['rounds'][round_index]['teams'][team2_index][
                                'opponents'].append(
                                {**game['team1'], 'spread': game['results']['team2_spread'],
                                 'total': game['results']['total'],
                                 'win_prob': game['results']['team2_wp']})
        if output_format == 'json':
            with open(output_dir + '.json', 'w', encoding='utf-8') as f:
                json.dump(matchup_dict, f)
        if output_format == 'csv':
            round_df = pd.DataFrame.from_dict(matchup_dict['regions'])
            r_df = round_df.explode('rounds', ignore_index=True)
            r_df['round'] = r_df['rounds'].apply(lambda x: x['id'])
            r_df['teams_list'] = r_df['rounds'].apply(lambda x: x['teams'])
            r_df = r_df.explode('teams_list', ignore_index=True)
            r_df['team'] = r_df['teams_list'].apply(lambda x: x['name'])
            r_df['seed'] = r_df['teams_list'].apply(lambda x: x['seed'])
            r_df['opponents_list'] = r_df['teams_list'].apply(lambda x: x['opponents'])
            r_df = r_df.explode('opponents_list', ignore_index=True)
            r_df['opponent'] = r_df['opponents_list'].apply(lambda x: x['name'])
            r_df['opp_seed'] = r_df['opponents_list'].apply(lambda x: x['seed'])
            r_df['spread'] = r_df['opponents_list'].apply(lambda x: x['spread'])
            r_df['total'] = r_df['opponents_list'].apply(lambda x: x['total'])
            r_df['win_prob'] = r_df['opponents_list'].apply(lambda x: x['win_prob'])
            r_df.rename(columns = {'id' : 'region_id'}, inplace=True)
            r_df = r_df[['region_id', 'round', 'team', 'seed', 'opponent', 'opp_seed', 'win_prob', 'spread', 'total']]
            r_df.to_csv(output_dir + '.csv', index=False)
        return matchup_dict

# sim = TournamentSim(iterations=10000, source='blended')
sim = TournamentSim(cached_result=True)
# sim.bracket_matchups(output_format='csv')
sim.team_summary(output_format='csv')
# sim.pool_value_pick10(output_format='csv')

# print(c)
