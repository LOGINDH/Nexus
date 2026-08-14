
from django.shortcuts import render

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

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

from .serializers import (
    UserSerializer,
    ShopCategorySerializer,
    ShopSerializer,
    ProductCategorySerializer,
    ProductSerializer,
    ProductVariationSerializer,
    CartSerializer,
    CartItemSerializer,
    OrderSerializer,
    OrderItemSerializer
)


# =========================================================
# USER REGISTER
# =========================================================

@api_view(['POST'])
def user_register(request):

    serializer = UserSerializer(
        data=request.data
    )

    if serializer.is_valid():

        user = serializer.save()

        return Response(
            {
                'message': 'User registered successfully',
                'user': UserSerializer(user).data
            },
            status=status.HTTP_201_CREATED
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


# =========================================================
# USER LOGIN
# =========================================================

@api_view(['POST'])
def user_login(request):

    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:

        return Response(
            {
                'error': 'Username and password are required'
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:

        user = User.objects.get(
            username=username
        )

    except User.DoesNotExist:

        return Response(
            {
                'error': 'Invalid username or password'
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Simple password comparison
    if user.password != password:

        return Response(
            {
                'error': 'Invalid username or password'
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    return Response(
        {
            'message': 'Login successful',
            'user': UserSerializer(user).data
        },
        status=status.HTTP_200_OK
    )


# =========================================================
# SHOP CATEGORY
# =========================================================

@api_view(['GET', 'POST'])
def shop_category(request):

    if request.method == 'GET':

        categories = ShopCategory.objects.all()

        serializer = ShopCategorySerializer(
            categories,
            many=True
        )

        return Response(
            serializer.data
        )

    elif request.method == 'POST':

        serializer = ShopCategorySerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# =========================================================
# SHOP
# =========================================================

@api_view(['GET', 'POST'])
def shop(request):

    if request.method == 'GET':

        shops = Shop.objects.all()

        serializer = ShopSerializer(
            shops,
            many=True
        )

        return Response(
            serializer.data
        )

    elif request.method == 'POST':

        serializer = ShopSerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# =========================================================
# PRODUCT CATEGORY
# =========================================================

@api_view(['GET', 'POST'])
def product_category(request):

    if request.method == 'GET':

        categories = ProductCategory.objects.all()

        serializer = ProductCategorySerializer(
            categories,
            many=True
        )

        return Response(
            serializer.data
        )

    elif request.method == 'POST':

        serializer = ProductCategorySerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# =========================================================
# PRODUCT
# =========================================================

@api_view(['GET', 'POST'])
def product(request):

    if request.method == 'GET':

        products = Product.objects.all()

        serializer = ProductSerializer(
            products,
            many=True
        )

        return Response(
            serializer.data
        )

    elif request.method == 'POST':

        serializer = ProductSerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# =========================================================
# PRODUCT VARIATION
# =========================================================

@api_view(['GET', 'POST'])
def product_variation(request):

    if request.method == 'GET':

        variations = ProductVariation.objects.all()

        serializer = ProductVariationSerializer(
            variations,
            many=True
        )

        return Response(
            serializer.data
        )

    elif request.method == 'POST':

        serializer = ProductVariationSerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# =========================================================
# CART
# =========================================================

@api_view(['GET', 'POST'])
def cart(request):

    if request.method == 'GET':

        carts = Cart.objects.all()

        serializer = CartSerializer(
            carts,
            many=True
        )

        return Response(
            serializer.data
        )

    elif request.method == 'POST':

        serializer = CartSerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# =========================================================
# CART ITEM
# =========================================================

@api_view(['GET', 'POST'])
def cart_item(request):

    if request.method == 'GET':

        items = CartItem.objects.all()

        serializer = CartItemSerializer(
            items,
            many=True
        )

        return Response(
            serializer.data
        )

    elif request.method == 'POST':

        serializer = CartItemSerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# =========================================================
# ORDER
# =========================================================

@api_view(['GET', 'POST'])
def order(request):

    if request.method == 'GET':

        orders = Order.objects.all()

        serializer = OrderSerializer(
            orders,
            many=True
        )

        return Response(
            serializer.data
        )

    elif request.method == 'POST':

        serializer = OrderSerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# =========================================================
# ORDER ITEM
# =========================================================

@api_view(['GET', 'POST'])
def order_item(request):

    if request.method == 'GET':

        items = OrderItem.objects.all()

        serializer = OrderItemSerializer(
            items,
            many=True
        )

        return Response(
            serializer.data
        )

    elif request.method == 'POST':

        serializer = OrderItemSerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
