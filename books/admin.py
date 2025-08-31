from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Book)
admin.site.register(Target)
admin.site.register(TargetName)
admin.site.register(Curation)
admin.site.register(Marc)