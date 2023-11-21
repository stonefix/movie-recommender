from django.contrib import admin

from .models import Movie, MyList, Myrating

# Register your models here.
admin.site.register(Movie)
admin.site.register(Myrating)
admin.site.register(MyList)
