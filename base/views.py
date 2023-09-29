from django.shortcuts import render, redirect
from django.http import HttpResponse
from bs4 import BeautifulSoup
import requests
import pandas as pd
import csv
from scipy.stats import poisson
import math
import heapq
import json
import os
from django.core.mail import send_mail
from django.views import View

# Create your views here.


def home(request):
    predictions = 'No Predictions Available'

    context = {'predictions':predictions}
    return render(request, 'scoracle.html', context)


class LeaguePrediction(View):
    template_name = 'scoracle.html'

    def get(self, request):
        predictions = 'No Predictions Available'

        context = {'predictions':predictions}
        return render(request, 'scoracle.html', context)
    def post(self, request):
        predictions = 'No Predictions Available'

        if request.method == 'POST':
            league_form = request.POST['league']
            league = str(league_form)
            urlavgtable = 'https://www.soccerstats.com/table.asp?league='+league+'&tid=d'
            urlfixture = 'https://www.soccerstats.com/latest.asp?league='+league
            # urlavgtable = urlavgtable
            # urlfixture = urlfixture
            try:
                # Print the league table into a csv file
                response = requests.get(urlavgtable)

                # Parse the HTML content using BeautifulSoup
                soup = BeautifulSoup(response.content, "html.parser")

                # Find the table element containing the data
                table = soup.find("table", {"id": "btable"})

                # Get the table header
                header = table.find_all("th")
                header = [h.text.strip() for h in header]

                # Get the table rows
                rows = table.find_all("tr")[1:]
                header_row = ['Team name', 'Scoredhome', 'Conc.', 'Total', 'Scored', 'Conc.', 'Total', 'Scored', 'Conc.', 'Total', 'GP']


                
                with open(f"csv/{league}.csv", mode='w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(header_row)

                    for row in rows[1:]:
                        cols = row.find_all('td')
                        cols = [col.text.strip() for col in cols]

                        writer.writerow(cols)

                # Send the fixture list and the predictions      
                res = requests.get(urlfixture)
                soup = BeautifulSoup(res.content, 'html.parser')

                odd_rows = soup.find_all('tr', {'class': 'odd', 'height': '32'})
                cols = []
                for row in odd_rows:
                    cols.extend(row.find_all('td', {'style': ['text-align:right;padding-right:8px;', 'text-align:left;padding-left:8px;']}))

                output = [col.text.strip() for col in cols]   

                with open(f"csv/{league}.csv", newline='') as csvfile:

                    # Create a CSV reader object
                    reader = csv.reader(csvfile)

                    # Create an empty list to hold the values in the first column
                    teams = []

                    # Iterate over each row in the CSV file
                    for row in reader:

                        # Append the value in the first column to the list
                        teams.append(row[0])

            # Print the first column values as a list
            # print(first_column_values[2])

                b_tags = soup.find_all('b')
                # if len(b_tags) >= 755:
                #     b_tags[752].text
                #     b_tags[754].text
                table = soup.find("table", style="margin-left:14px;margin-riht:14px;border:1px solid #aaaaaa;border-radius:12px;overflow:hidden;")

                Home_avg = float(100.000)
                if table:
                        # Find all <b> tags within the table
                        b_tags = table.find_all("b")

                        # Check if the 9th <b> tag exists
                        if len(b_tags) >= 9:
                            # Get the text from the 9th <b> tag
                            Home_avg = b_tags[8].text
                            
                # get away average for league
                Away_avg = float(100.000)
                if table:
                        # Find all <b> tags within the table
                        b_tags = table.find_all("b")

                        # Check if the 9th <b> tag exists
                        if len(b_tags) >= 11:
                            # Get the text from the 9th <b> tag
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
                        # print("Found at index:", my_list.index(first_item))
                        with open(f"csv/{league}.csv", 'r') as f:
                            reader = csv.reader(f)
                            row_index = 0
                            for row in reader:
                                if row_index == teams.index(first_item):  # row_index starts from 0, so we're looking at row 5 here
                                    row_list = row
                                    break  # stop iterating over rows once we find the desired row
                                row_index += 1
                    if second_item in teams:
                        # print("Found at index:", my_list.index(first_item))
                        with open(f"csv/{league}.csv", 'r') as f:
                            reader = csv.reader(f)
                            row_index = 0
                            for row in reader:
                                if row_index == teams.index(second_item):  # row_index starts from 0, so we're looking at row 5 here
                                    row_listaway = row
                                    break  # stop iterating over rows once we find the desired row
                                row_index += 1
                                # print(row_listaway[5])
                        H1 = ("{:0.2f}".format(float(row_list[1])/H3)) 
                        H2 = ("{:0.2f}".format(float(row_listaway[6])/H3)) 
                        Home_goal = ("{:0.2f}".format(float(H1) * float(H2) * float(H3)))
                        A1 = ("{:0.2f}".format(float(row_list[2])/A3)) 
                        A2 = ("{:0.2f}".format(float(row_listaway[5])/A3)) 
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
                # predictions = HttpResponse(predictions)
                

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