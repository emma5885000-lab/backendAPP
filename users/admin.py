from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'medecin', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations HealthTic', {'fields': ('role', 'medecin')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informations HealthTic', {'fields': ('role', 'medecin')}),
    )
