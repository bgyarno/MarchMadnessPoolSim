import requests
from lxml import html
from MarchMadnessPoolSim import team_index


# class bracket_object:
#     def __init__(self):
#         self.bracket_dict = {'regions': []}
# bracket = bracket_object
# print(bracket.bracket_dict())


def get_region_index(bracket_dict, region):
    return ([i for i in range(len(bracket_dict['regions'])) if bracket_dict['regions'][i]['id'] == region][0])


def get_game_id_index(bracket_dict, region, game_id):
    region_index = get_region_index(bracket_dict, region)
    return ([i for i in range(len(bracket_dict['regions'][region_index]['games'])) if
             bracket_dict['regions'][region_index]['games'][i]['game_id'] == game_id][0])


def build_region_object(bracket_dict, region, bracket_side, bracket_half):
    if region not in [bracket_dict['regions'][i]['id'] for i in range(len(bracket_dict['regions']))]:
        bracket_dict['regions'].append(
            {'id': region, 'bracket_side': bracket_side, 'bracket_half': bracket_half, 'games': []})


def build_game_object(bracket_dict, region, game_id):
    ## add game to dict
    region_index = get_region_index(bracket_dict, region)
    if game_id not in [bracket_dict['regions'][region_index]['games'][i]['game_id'] for i in
                       range(len(bracket_dict['regions'][region_index]['games']))]:
        bracket_dict['regions'][region_index]['games'].append({'game_id': game_id})


def add_teams(bracket_dict, team, seed, region, game_id, team_num):
    region_index = get_region_index(bracket_dict, region)
    game_id_index = get_game_id_index(bracket_dict, region, game_id)

    ## define team slot
    if team_num == 'TBD':
        if 'team1' in bracket_dict['regions'][region_index]['games'][game_id_index]:
            team_num = 'team2'
        else:
            team_num = 'team1'
    ## add teams and seeds to games
    if team_num == 'team1':
        bracket_dict['regions'][region_index]['games'][game_id_index]['team1'] = {'name': team,
                                                                                  'team_index': team_index()[team],
                                                                                  'seed': seed}
    if team_num == 'team2':
        bracket_dict['regions'][region_index]['games'][game_id_index]['team2'] = {'name': team,
                                                                                  'team_index': team_index()[team],
                                                                                  'seed': seed}


def team_name_validation(rows, seeded_rows):
    unmatched_teams = []
    for row_iter in seeded_rows:
        bracket_line_elem = rows[row_iter].xpath('td')
        bracket_team_pods = [td for td in bracket_line_elem if td.xpath('a/text()|span//text()')]
        teams = [td.xpath('a/text()|span//text()') for td in bracket_team_pods]
        ## remove team elements that do not contain team names
        teams_clean = format_teams(teams)
        if not (teams_clean):
            continue
        for team in teams_clean:
            try:
                team_index()[team[0]]
            except KeyError:
                unmatched_teams.append(team[0])
    if unmatched_teams:
        print('Error: Improper Team Indexing - Bracket Teams ' + str(unmatched_teams))
    else:
        print('Success: All Teams Properly Indexed - Bracket Teams')


def add_game_attribute(bracket_dict, region, game_id, attribute_name, key, value, value_type=str):
    region_index = get_region_index(bracket_dict, region)
    game_id_index = get_game_id_index(bracket_dict, region, game_id)
    if value_type == str:
        bracket_dict['regions'][region_index]['games'][game_id_index][attribute_name] = {key: value}
    if value_type == list:
        try:
            current_value = bracket_dict['regions'][region_index]['games'][game_id_index][attribute_name][key]
            current_value.append(value)
            bracket_dict['regions'][region_index]['games'][game_id_index][attribute_name] = {
                key: current_value}
        except KeyError:
            bracket_dict['regions'][region_index]['games'][game_id_index][attribute_name] = {key: [value]}


def build_regional_round(bracket_dict, region_object, round_name, predecessor_round_name):
    game_iter = 0
    ## build successor games for round of 64
    for game in [i for i in region_object['games'] if
                 'b' not in i['game_id'] and i['round']['name'] == predecessor_round_name]:
        max_game = max(
            [int(j['game_id']) for i in bracket_dict['regions'] for j in i['games'] if not 'b' in j['game_id']])
        ## create new game as successor to this game
        if game_iter % 2 == 0:
            new_game_id = str(max_game + 1)
            build_game_object(bracket_dict, region_object['id'], new_game_id)
            add_game_attribute(bracket_dict, region_object['id'], new_game_id, 'round', 'name', round_name)
        add_game_attribute(bracket_dict, region_object['id'], game['game_id'], 'successor', 'game_id', new_game_id)
        add_game_attribute(bracket_dict, region_object['id'], new_game_id, 'predecessor', 'game_id', game['game_id'],
                           value_type=list)
        game_iter += 1


def build_finals_round(bracket_dict, region_object, round_name, predecessor_round_name, finals_region_num):
    game_iter = 0
    for semifinal_side in ['left', 'right']:
        regions = [i for i in region_object if i['bracket_side'] == semifinal_side]
        for region in regions:
            for game in [i for i in region['games'] if i['round']['name'] == predecessor_round_name]:
                max_game = max(
                    [int(j['game_id']) for i in region_object for j in i['games'] if not 'b' in j['game_id']])
                ## create new game as successor to this game
                if game_iter % 2 == 0:
                    new_game_id = str(max_game + 1)
                    build_game_object(bracket_dict, finals_region_num, new_game_id)
                    add_game_attribute(bracket_dict, finals_region_num, new_game_id, 'round', 'name', round_name)
                add_game_attribute(bracket_dict, finals_region_num, new_game_id, 'predecessor', 'game_id',
                                   game['game_id'], value_type=list)
                add_game_attribute(bracket_dict, region['id'], game['game_id'], 'successor', 'game_id', new_game_id)
                game_iter += 1


def format_teams(team_list):
    for team_iter in range(len(team_list)):
        try:
            team_list[team_iter].remove(u'\xa0/\xa0')
        except ValueError:
            try:
                team_list[team_iter].remove(u'\xa0')
            except ValueError:
                try:
                    team_list[team_iter].remove(u'/\xa0')
                except ValueError:
                    continue
    teams_clean = []
    for i in range(len(team_list)):
        if team_list[i] != []:
            teams_clean.append([team.strip() for team in team_list[i]])
    return (teams_clean)


class Bracket:
    def __init__(self):
        self.bracket_dict = {'regions': []}

    def seed_bracket(self):
        '''initialize bracket with Round of 64 and First Four seeding'''
        url = 'https://www.collegesportsmadness.com/mens-basketball/bracketology'
        page = requests.get(url)
        tree = html.fromstring(page.content)
        rows = tree.xpath('//tbody/tr')
        seeded_rows = [i for i in range(1, len(rows)) if rows[i].xpath('td/text()')]
        # self.bracket_dict = {'regions': []}
        bracket_half = 0
        bracket_sides = ['left', 'right']
        game_ids = ['1', '2']
        matchup_iter = 0
        game_line_iter = 1
        region_ids = [1, 2]
        initial_seed_flag = 1
        ## validate team names in bracket are indexed
        team_name_validation(rows, seeded_rows)
        for row_iter in seeded_rows:
            seeds = rows[row_iter].xpath('td/text()')
            bracket_line_elem = rows[row_iter].xpath('td')
            edge_bracket = [(0, 5), (-5, -1)]  ## td elements from edge of bracket to consider for initial seeding
            bracket_team_pods = [td for start, finish in edge_bracket for td in bracket_line_elem[start:finish] if
                                 td.xpath('a/text()|span//text()')]
            teams = [td.xpath('a/text()|span//text()') for td in bracket_team_pods]
            ## remove team elements that do not contain team names
            teams_clean = format_teams(teams)
            if not (teams_clean):
                continue
            ## change bracket half and region IDs when #1 seed encountered
            if seeds[0] == '1':
                bracket_half += 1
                if bracket_half != initial_seed_flag:
                    region_ids = [region_ids[0] + 2, region_ids[1] + 2]
            ## iterate over game lines and build bracket game objects
            for game_line in teams_clean:
                game_line_index = teams_clean.index(game_line)
                region = region_ids[game_line_index]
                bracket_side = bracket_sides[game_line_index]
                game_id = game_ids[game_line_index]
                seed = seeds[game_line_index]

                ## add region to bracket_dict if not already existing
                build_region_object(self.bracket_dict, region, bracket_side, bracket_half)

                if len(game_line) == 1:
                    ## assign game_id and team if standard first round game
                    team = game_line[0]
                else:
                    ## assign game ID and team as TBD for game with first four predecessor, build game objects for first four
                    team = 'TBD'
                    sub_matchup_iter = 0
                    sub_game_id = game_ids[game_line_index] + 'b'
                    add_game_attribute(self.bracket_dict, region, game_id, 'predecessor', 'game_id', sub_game_id,
                                       value_type=list)

                    ## iterate over teams in play-in games and build bracket game objects and dependencies
                    for sub_team in game_line:
                        ## add game and dependencies
                        build_game_object(self.bracket_dict, region, sub_game_id)
                        add_game_attribute(self.bracket_dict, region, sub_game_id, 'successor', 'game_id', game_id)
                        add_game_attribute(self.bracket_dict, region, sub_game_id, 'round', 'name', 'First Four')
                        ## add teams and seeds to games
                        if sub_matchup_iter % 2 == 0:
                            add_teams(self.bracket_dict, sub_team, seed, region, sub_game_id, 'team1')
                        if sub_matchup_iter % 2 == 1:
                            add_teams(self.bracket_dict, sub_team, seed, region, sub_game_id, 'team2')
                        sub_matchup_iter += 1
                ## add game
                build_game_object(self.bracket_dict, region, game_id)
                add_game_attribute(self.bracket_dict, region, game_id, 'round', 'name', 'Round of 64')
                ## add teams and seeds to games
                if matchup_iter % 2 == 0:
                    add_teams(self.bracket_dict, team, seed, region, game_id, 'team1')
                if matchup_iter % 2 == 1:
                    add_teams(self.bracket_dict, team, seed, region, game_id, 'team2')

                ## update game ID's if all 4 games in pod have been added
                if game_line_iter % 4 == 0 and matchup_iter != 0:
                    game_ids = [str(int(game_ids[0]) + 2), str(int(game_ids[1]) + 2)]
                game_line_iter += 1
            matchup_iter += 1
        return (self.bracket_dict)

    def build_bracket(self):
        '''build bracket game objects for post Round of 64 games, with upstream and downstream dependencies'''
        for region in self.bracket_dict['regions']:
            ## build successor games for round of 64
            build_regional_round(self.bracket_dict, region, 'Round of 32', 'Round of 64')

            ## build successor games for round of 32
            build_regional_round(self.bracket_dict, region, 'Sweet 16', 'Round of 32')

            ## build successor games for Sweet 16
            build_regional_round(self.bracket_dict, region, 'Elite 8', 'Sweet 16')

        ## add new region for Final 4
        finals_region = len([i for i in self.bracket_dict['regions']]) + 1
        build_region_object(self.bracket_dict, finals_region, 'Final 4', 'Final 4')

        ## build successor games for Elite 8
        build_finals_round(self.bracket_dict, self.bracket_dict['regions'], 'Final 4', 'Elite 8', finals_region)

        ## build successor game for final 4
        finals_region_object = [i for i in self.bracket_dict['regions'] if i['id'] == finals_region][0]
        build_regional_round(self.bracket_dict, finals_region_object, 'Championship Game', 'Final 4')

    def initialize_bracket(self):
        '''build bracket with inital seeding and all downstream games'''
        self.seed_bracket()
        self.build_bracket()

        return (self.bracket_dict)
