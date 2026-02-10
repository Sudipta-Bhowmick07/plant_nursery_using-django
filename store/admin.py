from django.contrib import admin
from .models import Plant, Category, Order, OrderItem, CartItem


# =========================
# CATEGORY
# =========================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


# =========================
# PLANTS
# =========================
@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price", "stock", "available", "category")
    list_filter = ("available", "category")
    search_fields = ("name",)


# =========================
# ORDER ITEMS (inline inside order)
# =========================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


# =========================
# ORDERS
# =========================
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "total", "created_at", "city", "pincode")
    search_fields = ("user__username", "city", "pincode")
    list_filter = ("status","created_at", "city")
    inlines = [OrderItemInline]


# =========================
# CART (optional view)
# =========================
@admin.register(CartItem)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "plant", "quantity")
