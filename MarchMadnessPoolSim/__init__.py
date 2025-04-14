import csv

def team_index():
    file = open('./team_index.csv', "rU")
    reader = csv.reader(file, delimiter=',')
    team_dict = {}
    next(reader)
    for column in reader:
            team_dict[column[1]] = column[0]
    return(team_dict)

def spread_win_rates():
    file = open('./spread_win_rates.csv', "rU")
    reader = csv.reader(file, delimiter=',')
    lookup_dict = {}
    next(reader)
    for column in reader:
        lookup_dict[column[0]] = float(column[15])
    return (lookup_dict)
