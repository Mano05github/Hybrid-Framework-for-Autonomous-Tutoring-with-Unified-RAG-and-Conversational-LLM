from django.urls import path
from . import views

urlpatterns = [
    path('session/start/',        views.StartSessionView.as_view(),  name='pbl_session_start'),
    path('session/<uuid:session_id>/', views.SessionDetailView.as_view(), name='pbl_session_detail'),
    path('graph/<int:subject_id>/', views.SubjectGraphView.as_view(),  name='pbl_subject_graph'),
]
