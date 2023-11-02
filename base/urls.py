from django.urls import path, include
from . import views
from .views import LeaguePrediction, XPrediction

urlpatterns = [
    path('', views.home, name='home'),
    path('leagueprediction/', LeaguePrediction.as_view(), name="leagueprediction"),
    # path('matchprediction/', MatchPrediction.as_view(), name="matchprediction"),
    path('contact/', views.contact, name='contact'),
    path('xprediction/', XPrediction.as_view(), name="xprediction"),
    path('outcome', views.outcome, name='outcome'),
]
