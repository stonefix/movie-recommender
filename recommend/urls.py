from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("signup/", views.sign_up, name="signup"),
    path("login/", views.authorization, name="login"),
    path("logout/", views.logout_with_redirect, name="logout"),
    path("<int:movie_id>/", views.detail, name="detail"),
    path("watch/", views.watch, name="watch"),
    path("recommend/", views.recommend, name="recommend"),
]
