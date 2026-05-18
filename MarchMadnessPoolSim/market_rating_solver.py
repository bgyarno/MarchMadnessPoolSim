import pandas as pd
import numpy as np
from scipy.optimize import minimize
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import lsqr


def solve_team_ratings(df, time_decay=None):
    df = df.copy()

    required_cols = ["team", "opponent", "points_scored", "hfa"]
    for c in required_cols:
        if c not in df.columns:
            raise ValueError(f"Missing column: {c}")

    if time_decay is not None and "date" not in df.columns:
        raise ValueError("date column required when using time_decay")

    schools = sorted(set(df["team"]).union(set(df["opponent"])))
    n_teams = len(schools)

    team_index = {t: i for i, t in enumerate(schools)}

    n_games = len(df)
    n_vars = 2 + 2 * n_teams

    X = np.zeros((n_games, n_vars))
    y = df["points_scored"].values

    for r, row in enumerate(df.itertuples()):
        team = team_index[row.team]
        opp = team_index[row.opponent]

        X[r, 0] = 1
        X[r, 1] = row.hfa
        X[r, 2 + team] = 1
        X[r, 2 + n_teams + opp] = 1

    # ---------------------------
    # Time decay weighting
    # ---------------------------

    weights = np.ones(n_games)

    if time_decay is not None:
        df["date"] = pd.to_datetime(df["date"])
        newest_date = df["date"].max()

        age_days = (newest_date - df["date"]).dt.days.values

        weights = np.exp(-time_decay * age_days)

    # ---------------------------
    # Objective function
    # ---------------------------

    def objective(beta):

        residuals = y - X @ beta
        weighted = weights * residuals ** 2
        return np.sum(weighted)

    # ---------------------------
    # Constraints
    # ---------------------------

    def offense_sum(beta):
        return np.sum(beta[2:2 + n_teams])

    def defense_sum(beta):
        return np.sum(beta[2 + n_teams:])

    constraints = [
        {"type": "eq", "fun": offense_sum},
        {"type": "eq", "fun": defense_sum},
        {"type": "ineq", "fun": lambda b: b[0]}  # avg_points >= 0
    ]

    beta0 = np.zeros(n_vars)
    beta0[0] = df["points_scored"].mean()

    result = minimize(
        objective,
        beta0,
        constraints=constraints,
        method="SLSQP"
    )

    beta = result.x

    avg_points = beta[0]
    HFA = beta[1]

    offense = beta[2:2 + n_teams]
    defense = beta[2 + n_teams:]

    results_df = pd.DataFrame({
        "school": schools,
        "offense_rating": offense,
        "defense_rating": defense
    })

    results_df["avg_points"] = avg_points
    results_df["HFA"] = HFA
    results_df['net'] = results_df['offense_rating'] - results_df['defense_rating']
    return results_df


def solve_team_pace_ratings(df, decay=None, max_iter=25, tol=1e-6, per_100=False):
    df = df.copy()

    schools = sorted(set(df.team).union(df.opponent))
    n_teams = len(schools)
    n_games = len(df)

    team_index = {t: i for i, t in enumerate(schools)}

    team_ids = df.team.map(team_index).values
    opp_ids = df.opponent.map(team_index).values

    points = df.points_scored.values
    hfa = df.hfa.values

    rows = np.arange(n_games)

    T_team = csr_matrix((np.ones(n_games), (rows, team_ids)), shape=(n_games, n_teams))
    T_opp = csr_matrix((np.ones(n_games), (rows, opp_ids)), shape=(n_games, n_teams))

    weights = np.ones(n_games)

    if decay is not None:
        df["date"] = pd.to_datetime(df["date"])
        newest = df.date.max()
        age = (newest - df.date).dt.days.values
        weights = np.exp(-decay * age)

    W = np.sqrt(weights)

    off = np.zeros(n_teams)
    deff = np.zeros(n_teams)
    pace = np.zeros(n_teams)

    avg_points = points.mean()
    avg_pace = 70
    HFA = 0

    for _ in range(max_iter):

        prev = np.concatenate([off, deff, pace, [avg_points, avg_pace]])

        # ----- STEP 1: scoring -----
        pace_factor = avg_pace + pace[team_ids] + pace[opp_ids]

        y = points / pace_factor

        X = np.column_stack([
            np.ones(n_games),
            hfa,
            T_team.toarray(),
            T_opp.toarray()
        ])

        Xw = X * W[:, None]
        yw = y * W

        beta = lsqr(Xw, yw)[0]

        avg_points = beta[0]
        HFA = beta[1]

        off = beta[2:2 + n_teams]
        deff = beta[2 + n_teams:2 + 2 * n_teams]

        off -= off.mean()
        deff -= deff.mean()

        # ----- STEP 2: pace -----
        scoring = avg_points + HFA * hfa + off[team_ids] + deff[opp_ids]

        y = points / scoring

        X = np.column_stack([
            np.ones(n_games),
            T_team.toarray(),
            T_opp.toarray()
        ])

        Xw = X * W[:, None]
        yw = y * W

        beta = lsqr(Xw, yw)[0]

        avg_pace = beta[0]
        pace = beta[1:1 + n_teams]

        pace -= pace.mean()

        curr = np.concatenate([off, deff, pace, [avg_points, avg_pace]])

        if np.linalg.norm(curr - prev) < tol:
            break

    # ---- convert to per 100 possessions if requested ----
    if per_100:
        scale = 100
        off = off * scale
        deff = deff * scale
        avg_points = avg_points * scale
        HFA = HFA * scale

    results = pd.DataFrame({
        "school": schools,
        "offense_rating": off,
        "defense_rating": deff,
        "pace_rating": pace
    })

    results["avg_points"] = avg_points
    results["avg_pace"] = avg_pace
    results["HFA"] = HFA
    results["adj_oe"] = results["offense_rating"] + results["avg_points"]
    results["adj_de"] = results["defense_rating"] + results["avg_points"]
    results["adj_tempo"] = results["pace_rating"] + results["avg_pace"]

    results = results[["school", "adj_oe", "adj_de", "adj_tempo"]]
    return results


df = pd.read_csv('./market_odds.csv')
ratings = solve_team_pace_ratings(df, decay=.07, per_100=True)
ratings_df = pd.DataFrame(ratings)
ratings_df.to_csv('./market_ratings.csv', index=False)
