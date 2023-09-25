from django.urls import path, include
from . import views
from .views import LeaguePrediction, MatchPrediction

urlpatterns = [
    path('', views.home, name='home'),
    path('leagueprediction/', LeaguePrediction.as_view(), name="leagueprediction"),
    path('matchprediction/', MatchPrediction.as_view(), name="matchprediction"),
]