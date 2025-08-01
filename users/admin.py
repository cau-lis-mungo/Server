from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserStatus

# Register your models here.

class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ('username', 'name', 'user_type', 'is_staff')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('name', 'phone', 'user_type', 'status')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'name', 'user_type'),
        }),
    )
    search_fields = ('username',)
    ordering = ('username',)

admin.site.register(User, UserAdmin)
admin.site.register(UserStatus)
