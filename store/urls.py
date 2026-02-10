from django.urls import path
from . import views

urlpatterns = [
    path('', views.plant_list, name='plant_list'),
    path('plant/<int:id>/', views.plant_detail, name='plant_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('remove/<int:id>/', views.remove_from_cart, name='remove_from_cart'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    path("payment/<int:order_id>/", views.payment_page, name="payment_page"),
    path("register/", views.register, name="register"),
    

]
