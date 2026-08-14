
from rest_framework import serializers

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
    OrderItem
)


# =========================================================
# USER SERIALIZER
# =========================================================

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User

        fields = [
            'id',
            'username',
            'email',
            'password',
            'phone',
            'address',
            'created_at',
        ]

        extra_kwargs = {
            'password': {
                'write_only': True
            }
        }

    def create(self, validated_data):

        return User.objects.create(
            **validated_data
        )


# =========================================================
# SHOP CATEGORY SERIALIZER
# =========================================================

class ShopCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = ShopCategory
        fields = '__all__'


# =========================================================
# SHOP SERIALIZER
# =========================================================

class ShopSerializer(serializers.ModelSerializer):

    class Meta:
        model = Shop
        fields = '__all__'


# =========================================================
# PRODUCT CATEGORY SERIALIZER
# =========================================================

class ProductCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductCategory
        fields = '__all__'


# =========================================================
# PRODUCT SERIALIZER
# =========================================================

class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = '__all__'


# =========================================================
# PRODUCT VARIATION SERIALIZER
# =========================================================

class ProductVariationSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductVariation
        fields = '__all__'


# =========================================================
# CART ITEM SERIALIZER
# =========================================================

class CartItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = CartItem
        fields = '__all__'


# =========================================================
# CART SERIALIZER
# =========================================================

class CartSerializer(serializers.ModelSerializer):

    items = CartItemSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Cart

        fields = [
            'id',
            'user',
            'created_at',
            'updated_at',
            'items',
        ]


# =========================================================
# ORDER ITEM SERIALIZER
# =========================================================

class OrderItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderItem
        fields = '__all__'


# =========================================================
# ORDER SERIALIZER
# =========================================================

class OrderSerializer(serializers.ModelSerializer):

    items = OrderItemSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Order

        fields = [
            'id',
            'user',
            'status',
            'total_amount',
            'shipping_address',
            'phone',
            'created_at',
            'updated_at',
            'items',
        ]

