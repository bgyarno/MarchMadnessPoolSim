import requests
from lxml import html
from MarchMadnessPoolSim import team_index
import statistics


# class TeamDict:
#     def __init__(self):
#         self.team_dict = {}
#         self.generate_team_dict()
def get_torvik():
    url = 'https://barttorvik.com/#'
    page = requests.get(url)
    tree = html.fromstring(page.content)

    teams = tree.xpath('//td[@class="teamname"]/a/text()')
    adj_oe = tree.xpath('//td[@class="1  "]/text()')
    adj_de = tree.xpath('//td[@class="2  "]/text()')
    barthag = tree.xpath('//td[@class="3  "]/text()')
    adj_tempo = tree.xpath('//td[@class="26 mobileout"]/text()')

    if len(teams) == len(adj_oe) == len(adj_de) == len(barthag) == len(adj_tempo):
        torvik_dict = {}
        for i in range(len(teams)):
            torvik_dict[teams[i]] = {'adj_oe': adj_oe[i],
                                     'adj_de': adj_de[i],
                                     'barthag': barthag[i],
                                     'adj_tempo': adj_tempo[i],
                                     'name': teams[i],
                                     'team_index': team_index()[teams[i]]
                                     }
    else:
        print('!!! team and statistic list lengths do not match !!!')
        return (0)
    return (torvik_dict)


def torvik_name_validation(torvik_dict):
    unmatched_teams = []
    for key, value in torvik_dict.items():
        team = value['name']
        try:
            team_index()[team]
        except KeyError:
            unmatched_teams.append(team)
    if unmatched_teams:
        print('Error: Improper Team Indexing - Torvik Ratings ' + str(unmatched_teams))
    else:
        print('Success: All Teams Properly Indexed - Torvik Ratings')


def initialize_team_dict():
    ''' build dict with unique team_index keys and name values'''
    team_dict = {}
    for key, value in team_index().items():
        if not value in team_dict:
            team_dict[value] = {'names': [key]}
        else:
            team_dict[value]['names'].append(key)
    return (team_dict)


def add_torvik_ratings(team_dict):
    torvik_dict = get_torvik()
    torvik_name_validation(torvik_dict)
    for key, value in torvik_dict.items():
        team_dict[value['team_index']]['torvik_ratings'] = value
    return (team_dict)


def generate_team_dict():
    team_dict = initialize_team_dict()
    team_dict = add_torvik_ratings(team_dict)
    return (team_dict)


def avg_rating(team_dict, metric):
    off_ratings = [float(value['torvik_ratings'][metric]) for key, value in team_dict.items() if value['names'][0] != 'TBD']
    return (statistics.mean(off_ratings))


class Team:
    def __init__(self, team_dict, team_index):
        self.team_index = team_index
        self.team_dict = team_dict

    def team_ratings(self):
        team_ratings = self.team_dict[self.team_index]
        return (team_ratings)

    def team_name(self):
        team_name = self.team_dict[self.team_index]['names'][0]
        return (team_name)

    def off_rating(self):
        return (float(self.team_ratings()['torvik_ratings']['adj_oe']))

    def def_rating(self):
        return (float(self.team_ratings()['torvik_ratings']['adj_de']))

    def tempo_rating(self):
        return (float(self.team_ratings()['torvik_ratings']['adj_tempo']))

    def barthag(self):
        return (float(self.team_ratings()['torvik_ratings']['barthag']))

    def league_avg_off(self):
        return (avg_rating(self.team_dict, 'adj_oe'))

    def league_avg_def(self):
        return (avg_rating(self.team_dict, 'adj_de'))

    def league_avg_tempo(self):
        return (avg_rating(self.team_dict, 'adj_tempo'))
