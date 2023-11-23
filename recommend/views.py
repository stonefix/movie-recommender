import pandas as pd
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Case, Q, When
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render

from .forms import *
from .models import Movie, MyList, Myrating


def index(request):
    movies = Movie.objects.all()
    query = request.GET.get("q")

    if query:
        movies = Movie.objects.filter(Q(title__icontains=query)).distinct()
        return render(request, "recommend/list.html", {"movies": movies})

    return render(request, "recommend/list.html", {"movies": movies})

def detail(request, movie_id):
    if not request.user.is_authenticated:
        return redirect("login")
    if not request.user.is_active:
        raise Http404
    movies = get_object_or_404(Movie, id=movie_id)
    movie = Movie.objects.get(id=movie_id)
    
    temp = list(MyList.objects.all().values().filter(movie_id=movie_id,user=request.user))
    if temp:
        update = temp[0]["watch"]
    else:
        update = False
    if request.method == "POST":
        if "watch" in request.POST:
            update = True
 
            if MyList.objects.all().values().filter(movie_id=movie_id,user=request.user):
                MyList.objects.all().values().filter(movie_id=movie_id,user=request.user).update(watch=update)
            else:
                q=MyList(user=request.user,movie=movie,watch=update)
                q.save()
            if update:
                messages.success(request, "Фильм добавлен в ваш список!")
            else:
                messages.success(request, "Фильм удален из вашего списка!")
        
        elif "remove" in request.POST:
            update = False
            if MyList.objects.all().values().filter(movie_id=movie_id,user=request.user):
                MyList.objects.all().values().filter(movie_id=movie_id,user=request.user).update(watch=update)
            else:
                q=MyList(user=request.user,movie=movie,watch=update)
                q.save()
            if update:
                messages.success(request, "Фильм добавлен в ваш список!")
            else:
                messages.success(request, "Фильм удален из вашего списка!")
        else:
            rate = request.POST["rating"]
            if Myrating.objects.all().values().filter(movie_id=movie_id,user=request.user):
                Myrating.objects.all().values().filter(movie_id=movie_id,user=request.user).update(rating=rate)
            else:
                q=Myrating(user=request.user,movie=movie,rating=rate)
                q.save()

            messages.success(request, "Оценка добавлена!")

        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))
    out = list(Myrating.objects.filter(user=request.user.id).values())

    movie_rating = 0
    rate_flag = False
    for each in out:
        if each["movie_id"] == movie_id:
            movie_rating = each["rating"]
            rate_flag = True
            break

    context = {"movies": movies,"movie_rating":movie_rating,"rate_flag":rate_flag,"update":update}
    return render(request, "recommend/detail.html", context)


def watch(request):
    if not request.user.is_authenticated:
        return redirect("login")
    if not request.user.is_active:
        raise Http404

    movies = Movie.objects.filter(mylist__watch=True,mylist__user=request.user)
    query = request.GET.get("q")

    if query:
        movies = Movie.objects.filter(Q(title__icontains=query)).distinct()
        return render(request, "recommend/watch.html", {"movies": movies})

    return render(request, "recommend/watch.html", {"movies": movies})

# Получаем похожие фильмы из матрицы, на основе пользовательского рейтинга
def get_similar(movie_name, rating, corrMatrix):
    similar_ratings = corrMatrix[movie_name]*(rating-2.5)
    similar_ratings = similar_ratings.sort_values(ascending=False)
    return similar_ratings

# Рекомендации
def recommend(request):
    if not request.user.is_authenticated:
        return redirect("login")
    if not request.user.is_active:
        raise Http404

    movie_rating = pd.DataFrame(list(Myrating.objects.all().values()))
    new_user = movie_rating.user_id.unique().shape[0] # Берем количество строк
    current_user_id = request.user.id
    if current_user_id > new_user:
        movie = Movie.objects.get(id=68)
        q = Myrating(user=request.user,movie=movie,rating=0)
        q.save()

    userRatings = movie_rating.pivot_table(
        index=["user_id"],columns=["movie_id"],values="rating"
    )
    userRatings = userRatings.fillna(0,axis=1)
    # используем корреляцию пирсона для построения матрицы корреляций
    corrMatrix = userRatings.corr(method="pearson")

    user = pd.DataFrame(list(Myrating.objects.filter(user=request.user).values())).drop(
        ["user_id","id"],axis=1
    )
    user_filtered = [tuple(x) for x in user.values]
    movie_id_watched = [each[0] for each in user_filtered]

    similar_movies = pd.DataFrame()
    for movie,rating in user_filtered:
        similar_movies = similar_movies.append(get_similar(movie,rating,corrMatrix),ignore_index = True)

    movies_id = list(similar_movies.sum().sort_values(ascending=False).index)
    movies_id_recommend = [each for each in movies_id if each not in movie_id_watched]
    preserved = Case(
        *[When(pk=pk, then=pos) for pos, pk in enumerate(movies_id_recommend)]
    )
    movie_list=list(
        Movie.objects.filter(id__in = movies_id_recommend).order_by(preserved)[:10]
    )

    context = {"movie_list": movie_list}
    return render(request, "recommend/recommend.html", context)

# Регистрируем пользователя
def sign_up(request):
    form = UserForm(request.POST or None)

    if form.is_valid():
        user = form.save(commit=False)
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        
        if User.objects.filter(username=username).exists():
            return render(
                request, 
                "recommend/sign_up.html", 
                {"error_message": "Такой аккаунт уже существует"},
            )
        else:
            user.set_password(password)
            user.save()
            user = authenticate(username=username, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect("index")

    return render(request, "recommend/sign_up.html")

# авторизация пользователя
def authorization(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect("index")
            else:
                return render(
                    request, 
                    "recommend/login.html", 
                    {"error_message": "Ошибка, нету такого аккаунта"}
                )
        else:
            return render(
                request, "recommend/login.html", {"error_message": "Ошибка логина"}
            )

    return render(request, "recommend/login.html")

def logout_with_redirect(request):
    logout(request)
    return redirect("login")
