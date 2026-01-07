from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, views_users, views_shop, views_plans, views_public

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('onboarding/', views.onboarding, name='onboarding'),
    path('about/', views_public.about, name='about'),
    path('', views.index, name='home'),

    # Users Management (Pro)
    path('users/', views_users.user_list, name='user_list'),
    path('users/add/', views_users.user_add, name='user_add'),
    path('users/<int:user_id>/edit/', views_users.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', views_users.user_delete, name='user_delete'),
    
    # Shop Management (Pro Owner)
    path('shops/', views_shop.shop_list, name='shop_list'),
    path('shops/add/', views_shop.shop_add, name='shop_add'),
    path('shops/<int:shop_id>/switch/', views_shop.shop_switch, name='shop_switch'),
    
    # Plans Public
    path('plans/', views_plans.plans_view, name='plans'),
    path('plans/<int:plan_id>/subscribe/', views_plans.plan_subscribe, name='plan_subscribe'),
    # API sync endpoint for PWA offline queue
    path('api/sync/', views.api_sync, name='api_sync'),
]
