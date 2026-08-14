
from django.db import models


# =========================================================
# USER
# =========================================================

class User(models.Model):

    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('shopkeeper', 'Shop Keeper'),
    ]

    username = models.CharField(
        max_length=100,
        unique=True
    )

    email = models.EmailField(
        unique=True
    )

    password = models.CharField(
        max_length=255
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='customer'
    )

    phone = models.CharField(
        max_length=15,
        null=True,
        blank=True
    )

    address = models.TextField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.username} ({self.role})"


# =========================================================
# SHOP CATEGORY
# =========================================================

class ShopCategory(models.Model):

    name = models.CharField(
        max_length=100
    )

    description = models.TextField(
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name


# =========================================================
# SHOP
# =========================================================

class Shop(models.Model):

    name = models.CharField(
        max_length=150
    )

    category = models.ForeignKey(
        ShopCategory,
        on_delete=models.CASCADE,
        related_name='shops'
    )

    description = models.TextField(
        null=True,
        blank=True
    )

    address = models.TextField(
        null=True,
        blank=True
    )

    image = models.ImageField(
        upload_to='shops/',
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name


# =========================================================
# PRODUCT CATEGORY
# =========================================================

class ProductCategory(models.Model):

    name = models.CharField(
        max_length=100
    )

    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name='product_categories'
    )

    description = models.TextField(
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name


# =========================================================
# PRODUCT
# =========================================================

class Product(models.Model):

    name = models.CharField(
        max_length=200
    )

    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.CASCADE,
        related_name='products'
    )

    description = models.TextField(
        null=True,
        blank=True
    )

    image = models.ImageField(
        upload_to='products/',
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name


# =========================================================
# PRODUCT VARIATION
# =========================================================

class ProductVariation(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variations'
    )

    name = models.CharField(
        max_length=100
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    stock = models.PositiveIntegerField(
        default=0
    )

    description = models.TextField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.product.name} - {self.name}"


# =========================================================
# CART
# =========================================================

class Cart(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='carts'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Cart - {self.user.username}"


# =========================================================
# CART ITEM
# =========================================================

class CartItem(models.Model):

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product_variation = models.ForeignKey(
        ProductVariation,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )

    quantity = models.PositiveIntegerField(
        default=1
    )

    def __str__(self):
        return f"{self.product_variation.name} x {self.quantity}"


# =========================================================
# ORDER
# =========================================================

class Order(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    shipping_address = models.TextField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Order #{self.id}"


# =========================================================
# ORDER ITEM
# =========================================================

class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product_variation = models.ForeignKey(
        ProductVariation,
        on_delete=models.CASCADE,
        related_name='order_items'
    )

    quantity = models.PositiveIntegerField(
        default=1
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return f"Order #{self.order.id} - {self.product_variation.name}"
