from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from bs4 import BeautifulSoup
import requests
from scipy.stats import poisson
import math
import json
from django.core.mail import send_mail
from django.views import View
from datetime import datetime, date
from .models import Prediction


# In-memory storage for league data
# league_data = {}

# Create your views here.


def auto_test(request):
    send_mail(
        'New Visitor',
        'A visitor  has been on scoracle at ',
        'settings.EMAIL_HOST_USER',
        ['mezardini@gmail.com'],
        fail_silently=False,
    )
    return redirect('home')


def home(request):
    visitor_ip = visitor_ip = request.META.get('REMOTE_ADDR')
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # The IP addresses are usually comma-separated.
        ip_list = x_forwarded_for.split(',')
        # The client's IP address is the first in the list.
        visitor_ip = ip_list[0].strip()
    else:
        # If 'HTTP_X_FORWARDED_FOR' is not present, use 'REMOTE_ADDR'.
        visitor_ip = request.META.get('REMOTE_ADDR')

    # current_datetime = datetime.now()
    current_datetime = datetime.today().strftime("%d %b, %y %H:%M:%S")
    send_mail(
        'New Visitor',
        'A visitor ' + visitor_ip + ' has been on scoracle at ' + current_datetime,
        'settings.EMAIL_HOST_USER',
        ['mezardini@gmail.com'],
        fail_silently=False,
    )
    predictions = 'No Predictions Available'
    context = {'predictions': predictions}
    return render(request, 'scoracle.html', context)


class LeaguePrediction(View):
    template_name = 'scoracle.html'

    def get(self, request):
        predictions = 'No Predictions Available'
        context = {'predictions': predictions}
        return render(request, 'scoracle.html', context)

    def post(self, request):
        predictions = 'No Predictions Available'

        if request.method == 'POST':
            league_form = request.POST['league']
            league = str(league_form)
            urlavgtable = f'https://www.soccerstats.com/table.asp?league={league}&tid=d'
            urlfixture = f'https://www.soccerstats.com/latest.asp?league={league}'

            try:
                # Print the league table into in-memory data
                response = requests.get(urlavgtable)
                soup = BeautifulSoup(response.content, "html.parser")
                table = soup.find("table", {"id": "btable"})
                header = table.find_all("th")
                header = [h.text.strip() for h in header]
                rows = table.find_all("tr")[1:]
                league_data[league] = {'header': header, 'rows': []}

                for row in rows[1:]:
                    cols = row.find_all('td')
                    cols = [col.text.strip() for col in cols]
                    league_data[league]['rows'].append(cols)
                    print(league_data[league])

                # Send the fixture list and the predictions
                res = requests.get(urlfixture)
                soup = BeautifulSoup(res.content, 'html.parser')
                odd_rows = soup.find_all('tr', {'height': '32'})
                cols = []
                for row in odd_rows:
                    cols.extend(row.find_all('td', {'style': [
                                'text-align:right;padding-right:8px;', 'text-align:left;padding-left:8px;']}))

                output = [col.text.strip() for col in cols]

                teams = [row[0] for row in league_data[league]['rows']]

                b_tags = soup.find_all('b')
                table = soup.find(
                    "table", style="margin-left:14px;margin-riht:14px;border:1px solid #aaaaaa;border-radius:12px;overflow:hidden;")

                Home_avg = float(100.000)
                if table:
                    b_tags = table.find_all("b")
                    if len(b_tags) >= 9:
                        Home_avg = b_tags[8].text

                Away_avg = float(100.000)
                if table:
                    b_tags = table.find_all("b")
                    if len(b_tags) >= 11:
                        Away_avg = b_tags[10].text

                H3a = Home_avg
                A3a = Away_avg
                H3 = float(H3a)
                A3 = float(A3a)
                predictions_list = []

                for i in range(0, len(output), 2):
                    first_item = output[i]
                    second_item = output[i+1]
                    if first_item in teams:
                        row_list = league_data[league]['rows'][teams.index(
                            first_item)]
                        print(first_item)
                    if second_item in teams:
                        row_listaway = league_data[league]['rows'][teams.index(
                            second_item)]
                        print(second_item)

                    H1 = ("{:0.2f}".format(float(row_list[6])/H3))
                    print(row_list[6])
                    H2 = ("{:0.2f}".format(float(row_listaway[11])/H3))
                    print(row_listaway[11])
                    Home_goal = ("{:0.2f}".format(
                        float(H1) * float(H2) * float(H3)))
                    A1 = ("{:0.2f}".format(float(row_list[7])/A3))
                    print(row_list[7])
                    A2 = ("{:0.2f}".format(float(row_listaway[10])/A3))
                    print(row_listaway[10])
                    Away_goal = ("{:0.2f}".format(
                        float(A1) * float(A2) * float(A3)))
                    twomatch_goals_probability = ("{:0.2f}".format(
                        (1-poisson.cdf(k=2, mu=float(float(Home_goal) + float(Away_goal))))*100))
                    threematch_goals_probability = ("{:0.2f}".format(
                        (1-poisson.cdf(k=3, mu=float(float(Home_goal) + float(Away_goal))))*100))

                    lambda_home = float(Home_goal)
                    lambda_away = float(Away_goal)

                    score_probs = [[poisson.pmf(i, team_avg) for i in range(
                        0, 10)] for team_avg in [lambda_home, lambda_away]]

                    outcomes = [[i, j]
                                for i in range(0, 10) for j in range(0, 10)]

                    probs = [score_probs[0][i] * score_probs[1][j]
                             for i, j in outcomes]

                    most_likely_outcome = outcomes[probs.index(max(probs))]

                    most_likely_prob_percent = max(probs) * 100

                    response_data = [
                        {
                            'prediction': f"{first_item} {most_likely_outcome[0]} vs {second_item} {most_likely_outcome[1]}",
                            'over_2.5_prob': f"{threematch_goals_probability}%",
                            'over_1.5_prob': f"{twomatch_goals_probability}%"
                        },
                        # Add more predictions in a similar format if needed
                    ]
                    print(response_data)
                    predictions_list.extend(response_data)

                # Join predictions with newlines
                predictions = predictions_list

            except Exception as e:
                predictions = f'Error: {str(e)}'

        context = {'predictions': predictions}
        return render(request, 'scoracle.html', context)


def contact(request):
    if request.method == 'POST':
        body = request.POST['message']
        sender = request.POST['email']
        sender_name = request.POST['sender_name']

        send_mail(
            'Message from ' + sender + ' , ' + sender_name,
            body,
            'settings.EMAIL_HOST_USER',
            ['mezardini@gmail.com'],
            fail_silently=False,
        )

    return redirect('home')


def outcome(request):
    visitor_ip = visitor_ip = request.META.get('REMOTE_ADDR')
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # The IP addresses are usually comma-separated.
        ip_list = x_forwarded_for.split(',')
        # The client's IP address is the first in the list.
        visitor_ip = ip_list[0].strip()
    else:
        # If 'HTTP_X_FORWARDED_FOR' is not present, use 'REMOTE_ADDR'.
        visitor_ip = request.META.get('REMOTE_ADDR')

    # current_datetime = datetime.now()
    current_datetime = datetime.today().strftime("%d %b, %y %H:%M:%S")
    send_mail(
        'New Visitor',
        'A visitor ' + visitor_ip + ' has been on scoracle at ' + current_datetime,
        'settings.EMAIL_HOST_USER',
        ['mezardini@gmail.com'],
        fail_silently=False,
    )
    todays_predictions = 'No Predictions Available'
    today = date.today()
    print(today)
    if Prediction.objects.filter(date=today).exists():
        todays_predictions = Prediction.objects.get(date=today)

        # Assuming todays_predictions.content is a list of dictionaries
        predictions_data = todays_predictions.content

        # Sort the list based on 'over_1.5_prob' in descending order
        predictions_data = sorted(
            predictions_data, key=lambda x: x['over_1.5_prob'], reverse=True)
    else:
        return redirect('xpredict')
    context = {'predictions': todays_predictions.content, 'date': today}
    return render(request, 'outcome.html', context)


def pastpredictions(request):
    predictions = Prediction.objects.all().order_by('-date')
    context = {'predictions': predictions}
    return render(request, 'pastpredictions.html', context)


def fetch_data(url):
    try:
        session = requests.Session()
        response = session.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        return soup
    except Exception as e:
        return None


def calculate_poisson_probs(lambda_home, lambda_away):
    score_probs = [[poisson.pmf(i, team_avg) for i in range(
        0, 10)] for team_avg in [lambda_home, lambda_away]]
    outcomes = [[i, j] for i in range(0, 10) for j in range(0, 10)]
    probs = [score_probs[0][i] * score_probs[1][j] for i, j in outcomes]
    most_likely_outcome = outcomes[probs.index(max(probs))]
    most_likely_prob_percent = max(probs) * 100
    return most_likely_outcome, most_likely_prob_percent


def xpredict(request):
    base_url = 'https://www.soccerstats.com/'
    matchday_url = f'{base_url}matches.asp?matchday=1&listing=1'

    try:
        # Fetch data for matchday
        matchday_soup = fetch_data(matchday_url)
        if not matchday_soup:
            return redirect('outcome')

        table = matchday_soup.find('table', {'id': 'btable'})
        rows = table.find('tbody').find_all('tr')
        countries_to_check = [
            'spain',
            'england',
            'italy',
            'france',
            'germany',
            'germany2',
            'portugal',
            'netherlands',
            'netherlands2',
            'russia',
            'belgium',
            'turkey',
            'ukraine',
            'austria',
            'switzerland',
            'greece',
            'scotland',
            'croatia',
            'sweden',
            'norway',
            'denmark',
            'poland',
            'spain2',
            'england2',
            'italy2',
            'france2',

        ]
        unique_alt_texts = {row.find('td').get(
            'sorttable_customkey', '') for row in rows if row.get('height') == '34'}
        available_countries = [
            country for country in countries_to_check if country in unique_alt_texts]

        all_response_data = []

        for league in available_countries:
            # Fetch data for league table
            avgtable_url = f'{base_url}table.asp?league={league}&tid=d'
            avgtable_soup = fetch_data(avgtable_url)
            if not avgtable_soup:
                continue

            table = avgtable_soup.find("table", {"id": "btable"})
            header = [h.text.strip() for h in table.find_all("th")]
            rows = [row.find_all('td') for row in table.find_all("tr")[1:]]
            league_data = {'header': header, 'rows': [
                [col.text.strip() for col in row] for row in rows[1:]]}

            # Fetch data for fixture list and predictions
            fixture_url = f'{base_url}latest.asp?league={league}'
            fixture_soup = fetch_data(fixture_url)
            if not fixture_soup:
                continue

            odd_rows = fixture_soup.find_all('tr', {'height': '32'})
            cols = [col.text.strip() for row in odd_rows for col in row.find_all('td', {'style': [
                'text-align:right;padding-right:8px;', 'text-align:left;padding-left:8px;']})]

            # Extract teams and other information
            teams = [row[0] for row in league_data['rows']]
            home_avg = away_avg = 100.000
            table = fixture_soup.find(
                "table", style="margin-left:14px;margin-riht:14px;border:1px solid #aaaaaa;border-radius:12px;overflow:hidden;")
            if table:
                b_tags = table.find_all("b")
                if len(b_tags) >= 9:
                    home_avg = float(b_tags[8].text)
                if len(b_tags) >= 11:
                    away_avg = float(b_tags[10].text)

            # Perform calculations and store predictions
            for i in range(0, len(cols), 2):
                first_item, second_item = cols[i], cols[i + 1]
                if first_item in teams and second_item in teams:
                    home_index, away_index = teams.index(
                        first_item), teams.index(second_item)
                    row_list, row_list_away = league_data['rows'][home_index], league_data['rows'][away_index]

                    H1, H2 = float(
                        row_list[6]) / home_avg, float(row_list_away[11]) / home_avg
                    home_goal = float(H1) * float(H2) * home_avg
                    A1, A2 = float(
                        row_list[7]) / away_avg, float(row_list_away[10]) / away_avg
                    away_goal = float(A1) * float(A2) * away_avg

                    threematch_goals_probability = "{:0.2f}".format(
                        (1 - poisson.cdf(k=3, mu=home_goal + away_goal)) * 100)
                    twomatch_goals_probability = "{:0.2f}".format(
                        (1 - poisson.cdf(k=2, mu=home_goal + away_goal)) * 100)

                    most_likely_outcome, most_likely_prob_percent = calculate_poisson_probs(
                        home_goal, away_goal)

                    response_data = {
                        'home_team': first_item,
                        'home_goal': str(most_likely_outcome[0]),
                        'away_team': second_item,
                        'away_goal': str(most_likely_outcome[1]),
                        'over_2.5_prob': twomatch_goals_probability + '%',
                        'over_1.5_prob': threematch_goals_probability + '%',
                        'league': league,
                    }
                    all_response_data.append(response_data)
                    print(all_response_data)

        # Store predictions in the database
        predictionx = Prediction.objects.create(content=all_response_data)
        predictionx.save()
        return redirect('outcome')

    except Exception as e:
        return redirect('outcome')


class XPrediction(View):
    template_name = 'outcome.html'

    def get(self, request):
        predictions = 'No Predictions Available'
        context = {'predictions': predictions}
        return render(request, XPrediction.template_name, context)

    def post(self, request):
        predictions = 'No Predictions Available'

        if request.method == 'POST':
            # league_form = request.POST['league']
            # league = str(league_form)
            # urlavgtable = f'https://www.soccerstats.com/table.asp?league={league}&tid=d'
            # urlfixture = f'https://www.soccerstats.com/latest.asp?league={league}'
            url = 'https://www.soccerstats.com/matches.asp?matchday=3&listing=1'

            try:
                resx = requests.get(url)
                soup = BeautifulSoup(resx.content, "html.parser")

                table = soup.find('table', {'id': 'btable'})
                rows = table.find('tbody').find_all('tr')
                countries_to_check = [
                    'SPAIN',
                    'ENGLAND',
                    'ITALY',
                    'FRANCE',
                    'GERMANY',
                    'PORTUGAL',
                    'NETHERLANDS',
                    'RUSSIA',
                    'BELGIUM',
                    'TURKEY',
                    'UKRAINE',
                    'AUSTRIA',
                    'SWITZERLAND',
                    'GREECE',
                    'SCOTLAND',
                    'SPAIN2',
                    'ENGLAND2',
                    'ITALY2',
                    'FRANCE2',
                    'GERMANY2',
                    'NETHERLANDS2',
                ]
                # Create a set to store unique alt text values
                unique_alt_texts = set()

                # Loop through the rows to extract the alt text
                for row in rows:
                    # Check if the row has a height attribute equal to "34"
                    if row.get('height') == '34':
                        # Find the alt attribute in the row
                        alt = row.find('img').get('alt', '')

                        # Add the alt text to the set of unique alt texts
                        unique_alt_texts.add(alt)

                # Create a new list with countries that are available in the alt text
                available_countries = [
                    country for country in countries_to_check if country in unique_alt_texts]
                print("Available countries:", available_countries)

                all_response_data = []
                added_matches = set()
                # Print the league table into in-memory data
                for league in available_countries:
                    urlavgtable = f'https://www.soccerstats.com/table.asp?league={league}&tid=d'
                    urlfixture = f'https://www.soccerstats.com/latest.asp?league={league}'
                    response = requests.get(urlavgtable)
                    soup = BeautifulSoup(response.content, "html.parser")
                    table = soup.find("table", {"id": "btable"})
                    header = table.find_all("th")
                    header = [h.text.strip() for h in header]
                    rows = table.find_all("tr")[1:]
                    league_data[league] = {'header': header, 'rows': []}

                    for row in rows[1:]:
                        cols = row.find_all('td')
                        cols = [col.text.strip() for col in cols]
                        league_data[league]['rows'].append(cols)

                    # Send the fixture list and the predictions
                    res = requests.get(urlfixture)
                    soup = BeautifulSoup(res.content, 'html.parser')
                    odd_rows = soup.find_all('tr', {'height': '32'})
                    cols = []
                    for row in odd_rows:
                        cols.extend(row.find_all('td', {'style': [
                                    'text-align:right;padding-right:8px;', 'text-align:left;padding-left:8px;']}))

                    output = [col.text.strip() for col in cols]

                    teams = [row[0] for row in league_data[league]['rows']]

                    b_tags = soup.find_all('b')
                    table = soup.find(
                        "table", style="margin-left:14px;margin-riht:14px;border:1px solid #aaaaaa;border-radius:12px;overflow:hidden;")

                    Home_avg = float(100.000)
                    if table:
                        b_tags = table.find_all("b")
                        if len(b_tags) >= 9:
                            Home_avg = b_tags[8].text

                    Away_avg = float(100.000)
                    if table:
                        b_tags = table.find_all("b")
                        if len(b_tags) >= 11:
                            Away_avg = b_tags[10].text

                    H3a = Home_avg
                    A3a = Away_avg
                    H3 = float(H3a)
                    A3 = float(A3a)
                    predictions_list = []

                    for i in range(0, len(output), 2):
                        first_item = output[i]
                        second_item = output[i+1]
                        if first_item in teams:
                            row_list = league_data[league]['rows'][teams.index(
                                first_item)]
                            print(first_item)
                        if second_item in teams:
                            row_listaway = league_data[league]['rows'][teams.index(
                                second_item)]
                            print(second_item)

                        H1 = ("{:0.2f}".format(float(row_list[6])/H3))

                        H2 = ("{:0.2f}".format(float(row_listaway[11])/H3))

                        Home_goal = ("{:0.2f}".format(
                            float(H1) * float(H2) * float(H3)))
                        A1 = ("{:0.2f}".format(float(row_list[7])/A3))

                        A2 = ("{:0.2f}".format(float(row_listaway[10])/A3))

                        Away_goal = ("{:0.2f}".format(
                            float(A1) * float(A2) * float(A3)))
                        twomatch_goals_probability = ("{:0.2f}".format(
                            (1-poisson.cdf(k=2, mu=float(float(Home_goal) + float(Away_goal))))*100))
                        threematch_goals_probability = ("{:0.2f}".format(
                            (1-poisson.cdf(k=3, mu=float(float(Home_goal) + float(Away_goal))))*100))

                        lambda_home = float(Home_goal)
                        lambda_away = float(Away_goal)

                        score_probs = [[poisson.pmf(i, team_avg) for i in range(
                            0, 10)] for team_avg in [lambda_home, lambda_away]]

                        outcomes = [[i, j]
                                    for i in range(0, 10) for j in range(0, 10)]

                        probs = [score_probs[0][i] * score_probs[1][j]
                                 for i, j in outcomes]

                        most_likely_outcome = outcomes[probs.index(max(probs))]

                        most_likely_prob_percent = max(probs) * 100

                        response_data = [
                            {
                                'home_team': f"{first_item}",
                                'home_goal': f"{most_likely_outcome[0]}",
                                'away_team': f"{second_item}",
                                'away_goal': f"{most_likely_outcome[1]}",
                                'over_2.5_prob': f"{threematch_goals_probability}%",
                                'over_1.5_prob': f"{twomatch_goals_probability}%"
                            },
                            # Add more predictions in a similar format if needed
                        ]
                        all_response_data.extend(response_data)
                # for response_item in all_response_data:
                #     print(response_item)

                # Join predictions with newlines
                predictions = all_response_data
                predictionx = Prediction.objects.create(content=predictions)
                predictionx.save()

            except Exception as e:
                predictions = f'Error: {str(e)}'

        context = {'predictions': predictions}
        return render(request, XPrediction.template_name, context)


def vipsection(request):
    return render(request, 'vippage.html')


def error_404_view(request, exception):

    # we add the path to the 404.html file
    # here. The name of our HTML file is 404.html
    return render(request, '404.html')
