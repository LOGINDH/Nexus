from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import (
    User,
    ShopCategory,
    Shop,
    ProductCategory,
    Product,
    ProductVariation,
    Cart,
    CartItem,
    Order,
    OrderItem,
)


@admin.register(User)
class UserAdmin(ImportExportModelAdmin):
    pass


@admin.register(ShopCategory)
class ShopCategoryAdmin(ImportExportModelAdmin):
    pass


@admin.register(Shop)
class ShopAdmin(ImportExportModelAdmin):
    pass


@admin.register(ProductCategory)
class ProductCategoryAdmin(ImportExportModelAdmin):
    pass


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    pass


@admin.register(ProductVariation)
class ProductVariationAdmin(ImportExportModelAdmin):
    pass


@admin.register(Cart)
class CartAdmin(ImportExportModelAdmin):
    pass


@admin.register(CartItem)
class CartItemAdmin(ImportExportModelAdmin):
    pass


@admin.register(Order)
class OrderAdmin(ImportExportModelAdmin):
    pass


@admin.register(OrderItem)
class OrderItemAdmin(ImportExportModelAdmin):
    pass