from rest_framework import permissions


class IsManager(permissions.BasePermission):
    """Allows access to admins (superusers/staff) and users in the Manager group."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        return user.is_staff or user.groups.filter(name='Manager').exists()


class IsDeliveryCrew(permissions.BasePermission):
    """Allows access to users in the Delivery crew group."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        return user.groups.filter(name='Delivery crew').exists()


class IsCustomer(permissions.BasePermission):
    """A 'customer' is simply any authenticated user with no elevated role."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        return not (
            user.is_staff
            or user.groups.filter(name__in=['Manager', 'Delivery crew']).exists()
        )
