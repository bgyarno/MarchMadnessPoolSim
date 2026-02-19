import pandas as pd
from lxml import html
from MarchMadnessPoolSim import team_index
import statistics
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import csv


def get_torvik():
    url = 'https://barttorvik.com/#'

    # Configure headless Chrome
    options = Options()

    ## retreive webpage data and close driver
    driver = webdriver.Chrome(options=options)
    driver.get(url)

    # Wait up to 10 seconds for the element to be present in the DOM
    wait = WebDriverWait(driver, 10)
    wait.until(
        EC.presence_of_element_located((By.CLASS_NAME, "teamname"))
    )
    tree = html.fromstring(driver.page_source)
    driver.quit()

    ## parse html
    teams = tree.xpath('//td[@class="teamname"]/a/text()')
    adj_oe = tree.xpath('//td[@class="1  "]/text()')
    adj_de = tree.xpath('//td[@class="2  "]/text()')
    barthag = tree.xpath('//td[@class="3  "]/text()')
    adj_tempo = tree.xpath('//td[@class="26 mobileout"]/text()')
    if len(teams) == len(adj_oe) == len(adj_de) == len(barthag) == len(adj_tempo):
        torvik_dict = {}
        for i in range(len(teams)):
            torvik_dict[teams[i]] = {'adj_oe': float(adj_oe[i]),
                                     'adj_de': float(adj_de[i]),
                                     'barthag': float(barthag[i]),
                                     'adj_tempo': float(adj_tempo[i]),
                                     'name': teams[i],
                                     'team_index': team_index()[teams[i]]
                                     }
    else:
        print('!!! team and statistic list lengths do not match !!!')
        return (0)
    return (torvik_dict)


def name_validation(dict, source):
    unmatched_teams = []
    for key, value in dict.items():
        team = value['name']
        try:
            team_index()[team]
        except KeyError:
            unmatched_teams.append(team)
    if unmatched_teams:
        print('Error: Improper Team Indexing - ' + source + ' Ratings ' + str(unmatched_teams))
    else:
        print('Success: All Teams Properly Indexed - ' + source + ' Ratings')


def get_kenpom():
    url = 'https://kenpom.com/'

    # Configure headless Chrome
    options = Options()

    ## retreive webpage data and close driver
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    tree = html.fromstring(driver.page_source)
    driver.quit()

    ## parse html
    teams = tree.xpath('//table/tbody/tr/td[2]/a/text()')
    adj_oe = tree.xpath('//table/tbody/tr/td[6]/text()')
    adj_de = tree.xpath('//table/tbody/tr/td[8]/text()')
    adj_tempo = tree.xpath('//table/tbody/tr/td[10]/text()')

    if len(teams) == len(adj_oe) == len(adj_de) == len(adj_tempo):
        kenpom_dict = {}
        for i in range(len(teams)):
            kenpom_dict[teams[i]] = {'adj_oe': float(adj_oe[i]),
                                     'adj_de': float(adj_de[i]),
                                     'adj_tempo': float(adj_tempo[i]),
                                     'name': teams[i],
                                     'team_index': team_index()[teams[i]]
                                     }
    else:
        print('!!! team and statistic list lengths do not match !!!')
        return (0)

    return (kenpom_dict)


def get_manual(input_dir='./market_ratings.csv', adj_oe_col='adj_oe', adj_de_col='adj_de',
               adj_tempo_col='adj_tempo', team_col='school'):
    if input_dir.lower().endswith('.csv'):
        df = pd.read_csv(input_dir)
    adj_oe = df[adj_oe_col]
    adj_de = df[adj_de_col]
    adj_tempo = df[adj_tempo_col]
    teams = df[team_col]
    manual_dict = {}
    for i in range(len(teams)):
        manual_dict[teams[i]] = {'adj_oe': float(adj_oe[i]),
                                 'adj_de': float(adj_de[i]),
                                 'adj_tempo': float(adj_tempo[i]),
                                 'name': teams[i],
                                 'team_index': team_index()[teams[i]]
                                 }
    return manual_dict


def initialize_team_dict():
    ''' build dict with unique team_index keys and name values'''
    team_dict = {}
    for key, value in team_index().items():
        if not value in team_dict:
            team_dict[value] = {'names': [key]}
        else:
            team_dict[value]['names'].append(key)
    return (team_dict)


def add_ratings(ratings_dict, team_dict, source):
    if not source in ['torvik', 'kenpom', 'manual']:
        'Validation Failed: Improper Ratings source.  Options:  torvik, kenpom, manual"'
        return (0)

    name_validation(ratings_dict, source)
    for key, value in ratings_dict.items():
        team_dict[value['team_index']][source + '_ratings'] = value
    return (team_dict)


def blend_ratings(team_dict: dict, ratings: list, weights: list):
    ## validate weights
    if not weights:
        ## if no weights provided set to even distribution
        weights = [1.0 / len(ratings) for i in ratings]
    if len(ratings) != len(weights):
        print('Failure:  Ratings and Weight list lengths do not match')
        return (0)
    if sum(weights) != 1:
        print('Failure:  Weights do not add up to 100%')
        return (0)

    ## create blended ratings entry
    for key, value in team_dict.items():
        if key == '0':
            ## skip TBD team placholder used for first four placholder
            continue
        blended_dict = {}
        for metric in ['adj_oe', 'adj_de', 'adj_tempo']:
            metric_vals = []
            for r in ratings:
                metric_vals.append(value[r + '_ratings'][metric])
            weighted_val = sum([metric_vals[i] * weights[i] for i in range(len(metric_vals))])
            blended_dict[metric] = weighted_val
        team_dict[key]['blended_ratings'] = blended_dict

    return (team_dict)


def generate_team_dict(cached_ratings=False, ratings_dir='./team_dict.js', ratings=['torvik', 'kenpom', 'manual'],
                       blended=True,
                       weights=[]):
    if not weights:
        weights = [1.0 / float(len(ratings))] * len(ratings)
    if not cached_ratings:
        team_dict = initialize_team_dict()
        for r in ratings:
            dict = eval('get_' + r)()
            team_dict = add_ratings(dict, team_dict, r)

        if blended:
            team_dict = blend_ratings(team_dict, ratings, weights)
        with open(ratings_dir, 'w+', encoding='utf-8') as f:
            json.dump(team_dict, f)
    else:
        with open(ratings_dir, "r", encoding='utf-8') as f:
            team_dict = json.load(f)
    return (team_dict)


def avg_rating(team_dict, metric, source):
    off_ratings = [float(value[source + '_ratings'][metric]) for key, value in team_dict.items() if
                   value['names'][0] != 'TBD']
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

    def off_rating(self, source):
        return (float(self.team_ratings()[source + '_ratings']['adj_oe']))

    def def_rating(self, source):
        return (float(self.team_ratings()[source + '_ratings']['adj_de']))

    def tempo_rating(self, source):
        return (float(self.team_ratings()[source + '_ratings']['adj_tempo']))

    def barthag(self, source):
        return (float(self.team_ratings()[source + '_ratings']['barthag']))

    def league_avg_off(self, source):
        return (avg_rating(self.team_dict, 'adj_oe', source))

    def league_avg_def(self, source):
        return (avg_rating(self.team_dict, 'adj_de', source))

    def league_avg_tempo(self, source):
        return (avg_rating(self.team_dict, 'adj_tempo', source))
