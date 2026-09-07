from decimal import Decimal

from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

from .models import Category, MenuItem, Cart, Order, OrderItem
from .permissions import IsManager, IsDeliveryCrew
from .serializers import (
    CategorySerializer,
    MenuItemSerializer,
    UserSerializer,
    CartSerializer,
    OrderSerializer,
    OrderUpdateSerializer,
)


# ---------------------------------------------------------------------------
# Categories  (criteria 3 & 4: admin adds menu items / categories,
# criterion 13: customers can browse all categories)
# ---------------------------------------------------------------------------
class CategoriesView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [IsAuthenticated()]


# ---------------------------------------------------------------------------
# Menu items
# (criteria 3: admin adds menu items, 6: manager updates item of the day,
#  14-17: customers browse/filter/paginate/sort menu items)
# ---------------------------------------------------------------------------
class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.select_related('category').all()
    serializer_class = MenuItemSerializer
    filterset_fields = ['category__title', 'featured']
    search_fields = ['title', 'category__title']
    ordering_fields = ['price', 'title']

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsManager()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()

        category_name = self.request.query_params.get('category')
        if category_name:
            queryset = queryset.filter(category__title__iexact=category_name)

        to_price = self.request.query_params.get('to_price')
        if to_price:
            queryset = queryset.filter(price__lte=to_price)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # Manual pagination via ?page= & ?perpage= as commonly required
        perpage = request.query_params.get('perpage', 10)
        page = request.query_params.get('page', 1)
        try:
            perpage = int(perpage)
            page = int(page)
        except ValueError:
            perpage = 10
            page = 1

        from django.core.paginator import Paginator, EmptyPage
        paginator = Paginator(queryset, perpage)
        try:
            items = paginator.page(page)
        except EmptyPage:
            items = []

        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)


class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.select_related('category').all()
    serializer_class = MenuItemSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsManager()]


# ---------------------------------------------------------------------------
# Manager group management
# (criteria 1 & 2: admin assigns users to manager group / accesses it with admin token)
# ---------------------------------------------------------------------------
class ManagerUsersView(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return User.objects.filter(groups__name='Manager')

    def create(self, request, *args, **kwargs):
        username = request.data.get('username')
        if not username:
            return Response({'message': 'username is required'}, status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(User, username=username)
        managers = Group.objects.get(name='Manager')
        managers.user_set.add(user)
        return Response({'message': f'{username} added to the Manager group'}, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def remove_manager(request, pk):
    user = get_object_or_404(User, pk=pk)
    managers = Group.objects.get(name='Manager')
    managers.user_set.remove(user)
    return Response({'message': f'{user.username} removed from the Manager group'}, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Delivery crew group management
# (criterion 7: managers assign users to the delivery crew)
# ---------------------------------------------------------------------------
class DeliveryCrewUsersView(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        return User.objects.filter(groups__name='Delivery crew')

    def create(self, request, *args, **kwargs):
        username = request.data.get('username')
        if not username:
            return Response({'message': 'username is required'}, status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(User, username=username)
        crew = Group.objects.get(name='Delivery crew')
        crew.user_set.add(user)
        return Response({'message': f'{username} added to the Delivery crew group'}, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsManager])
def remove_delivery_crew(request, pk):
    user = get_object_or_404(User, pk=pk)
    crew = Group.objects.get(name='Delivery crew')
    crew.user_set.remove(user)
    return Response({'message': f'{user.username} removed from the Delivery crew group'}, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Cart
# (criteria 18 & 19: add to cart / view own cart items)
# ---------------------------------------------------------------------------
class CartView(generics.ListCreateAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        menuitem_id = request.data.get('menuitem_id')
        quantity = int(request.data.get('quantity', 1))
        menuitem = get_object_or_404(MenuItem, pk=menuitem_id)
        unit_price = menuitem.price
        price = unit_price * quantity

        cart_item, created = Cart.objects.update_or_create(
            user=request.user,
            menuitem=menuitem,
            defaults={'quantity': quantity, 'unit_price': unit_price, 'price': price},
        )
        serializer = self.get_serializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        Cart.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Orders
# (criteria 8, 9, 10, 20, 21)
# ---------------------------------------------------------------------------
class OrdersView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return OrderSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.groups.filter(name='Manager').exists():
            return Order.objects.all().prefetch_related('items__menuitem__category')
        if user.groups.filter(name='Delivery crew').exists():
            return Order.objects.filter(delivery_crew=user).prefetch_related('items__menuitem__category')
        return Order.objects.filter(user=user).prefetch_related('items__menuitem__category')

    def create(self, request, *args, **kwargs):
        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items.exists():
            return Response({'message': 'Your cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        total = sum((item.price for item in cart_items), Decimal('0.00'))
        order = Order.objects.create(user=request.user, total=total, status=False)

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                menuitem=item.menuitem,
                quantity=item.quantity,
                unit_price=item.unit_price,
                price=item.price,
            )
        cart_items.delete()

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SingleOrderView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all().prefetch_related('items__menuitem__category')

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return OrderUpdateSerializer
        return OrderSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        if self.request.method == 'DELETE':
            return [IsManager()]
        # PUT / PATCH: manager can assign crew & change status,
        # delivery crew can only flip the status of their own assigned order.
        return [IsAuthenticated()]

    def get_object(self):
        order = super().get_object()
        user = self.request.user

        if self.request.method == 'GET':
            allowed = (
                user.is_staff
                or user.groups.filter(name__in=['Manager', 'Delivery crew']).exists()
                or order.user == user
            )
            if not allowed:
                self.permission_denied(self.request)

        if self.request.method in ('PUT', 'PATCH'):
            is_manager = user.is_staff or user.groups.filter(name='Manager').exists()
            is_assigned_crew = (
                user.groups.filter(name='Delivery crew').exists() and order.delivery_crew == user
            )
            if not (is_manager or is_assigned_crew):
                self.permission_denied(self.request)

        return order

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        is_manager = user.is_staff or user.groups.filter(name='Manager').exists()

        if is_manager:
            # Manager can update delivery_crew and/or status
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        else:
            # Delivery crew: only allowed to update the 'status' field
            status_value = request.data.get('status')
            if status_value is None:
                return Response(
                    {'message': 'Delivery crew can only update the order status'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            instance.status = bool(int(status_value))
            instance.save()

        return Response(OrderSerializer(instance).data, status=status.HTTP_200_OK)
