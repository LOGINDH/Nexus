
from django.urls import path

from .views import (
    user_register,
    user_login,
    shop_category,
    shop,
    product_category,
    product,
    product_variation,
    cart,
    cart_item,
    order,
    order_item
)


urlpatterns = [

    # User
    path('register/', user_register),
    path('login/', user_login),

    # Shop
    path('shop-categories/', shop_category),
    path('shops/', shop),

    # Product
    path('product-categories/', product_category),
    path('products/', product),
    path('product-variations/', product_variation),

    # Cart
    path('carts/', cart),
    path('cart-items/', cart_item),

    # Order
    path('orders/', order),
    path('order-items/', order_item),
]
