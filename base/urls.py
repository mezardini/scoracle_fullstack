from django.urls import path, include
from . import views
from .views import LeaguePrediction, XPrediction

urlpatterns = [
    path('predictleague', views.home, name='home'),
    path('leagueprediction/', LeaguePrediction.as_view(), name="leagueprediction"),
    # path('matchprediction/', MatchPrediction.as_view(), name="matchprediction"),
    path('contact/', views.contact, name='contact'),
    path('xprediction/', XPrediction.as_view(), name="xprediction"),
    path('', views.outcome, name='outcome'),
    path('xpredict/', views.xpredict, name='xpredict'),
    path('pastpredictions/', views.pastpredictions, name='pastpredictions'),
    # path('vip/', views.vipsection, name='vipsection'),
    path('auto', views.auto_test, name='auto_test'),
]
