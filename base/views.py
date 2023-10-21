from django.shortcuts import render, redirect
from django.http import HttpResponse
from bs4 import BeautifulSoup
import requests
from scipy.stats import poisson
import math
import json
from django.core.mail import send_mail
from django.views import View
from datetime import datetime

# In-memory storage for league data
league_data = {}

# Create your views here.

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
                
                # Send the fixture list and the predictions
                res = requests.get(urlfixture)
                soup = BeautifulSoup(res.content, 'html.parser')
                odd_rows = soup.find_all('tr', {'bgcolor':'#fff5e6', 'height': '32'})
                cols = []
                for row in odd_rows:
                    cols.extend(row.find_all('td', {'style': ['text-align:right;padding-right:8px;', 'text-align:left;padding-left:8px;']}))

                output = [col.text.strip() for col in cols]

                teams = [row[0] for row in league_data[league]['rows']]

                b_tags = soup.find_all('b')
                table = soup.find("table", style="margin-left:14px;margin-riht:14px;border:1px solid #aaaaaa;border-radius:12px;overflow:hidden;")

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
                        row_list = league_data[league]['rows'][teams.index(first_item)]
                        print(first_item)
                    if second_item in teams:
                        row_listaway = league_data[league]['rows'][teams.index(second_item)]
                        print(second_item)

                    H1 = ("{:0.2f}".format(float(row_list[6])/H3))
                    print(row_list[6])
                    H2 = ("{:0.2f}".format(float(row_listaway[11])/H3))
                    print(row_listaway[11])
                    Home_goal = ("{:0.2f}".format(float(H1) * float(H2) * float(H3)))
                    A1 = ("{:0.2f}".format(float(row_list[7])/A3))
                    print(row_list[7])
                    A2 = ("{:0.2f}".format(float(row_listaway[10])/A3))
                    print(row_listaway[10])
                    Away_goal = ("{:0.2f}".format(float(A1) * float(A2) * float(A3)))
                    twomatch_goals_probability = ("{:0.2f}".format((1-poisson.cdf(k=2, mu=float(float(Home_goal) + float(Away_goal))))*100))
                    threematch_goals_probability = ("{:0.2f}".format((1-poisson.cdf(k=3, mu=float(float(Home_goal) + float(Away_goal))))*100))

                    lambda_home = float(Home_goal)
                    lambda_away = float(Away_goal)

                    score_probs = [[poisson.pmf(i, team_avg) for i in range(0, 10)] for team_avg in [lambda_home, lambda_away]]

                    outcomes = [[i, j] for i in range(0, 10) for j in range(0, 10)]

                    probs = [score_probs[0][i] * score_probs[1][j] for i, j in outcomes]

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