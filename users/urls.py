from django.urls import path
from .views import RegisterView, LoginView, doctor_list, patient_list, contacts_list

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('doctors/', doctor_list, name='doctor-list'),
    path('patients/', patient_list, name='patient-list'),
    path('contacts/', contacts_list, name='contacts-list'),
]
