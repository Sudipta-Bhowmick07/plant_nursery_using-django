from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings


from .models import (
    Plant, Category,
    CartItem,
    Order, OrderItem
)

# =====================================================
# PLANT LIST
# =====================================================
def plant_list(request):
    plants = Plant.objects.filter(available=True)
    categories = Category.objects.all()

    category_id = request.GET.get('category')
    if category_id:
        plants = plants.filter(category_id=category_id)

    query = request.GET.get('q')
    if query:
        plants = plants.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

    return render(request, 'store/plant_list.html', {
        'plants': plants,
        'categories': categories
    })


# =====================================================
# PLANT DETAIL + ADD TO CART
# =====================================================
def plant_detail(request, id):
    plant = get_object_or_404(Plant, id=id)

    if request.method == "POST":
        qty = int(request.POST.get('quantity', 1))

        if qty > plant.stock:
            qty = plant.stock

        # LOGGED USER → DB CART
        if request.user.is_authenticated:
            item, created = CartItem.objects.get_or_create(
                user=request.user,
                plant=plant
            )

            if created:
                item.quantity = qty
            else:
                new_qty = item.quantity + qty
                if new_qty > plant.stock:
                    new_qty = plant.stock
                item.quantity = new_qty

            item.save()

        # GUEST → SESSION CART
        else:
            cart = request.session.get('cart', {})
            current_qty = cart.get(str(id), 0)
            new_qty = current_qty + qty

            if new_qty > plant.stock:
                new_qty = plant.stock

            cart[str(id)] = new_qty
            request.session['cart'] = cart

        messages.success(request, f"{plant.name} added to cart 🛒")
        return redirect('cart')

    return render(request, 'store/plant_detail.html', {'plant': plant})


# =====================================================
# CART PAGE
# =====================================================
def cart_view(request):

    if request.user.is_authenticated:
        items = CartItem.objects.filter(user=request.user)
        total = sum(item.subtotal() for item in items)

        return render(request, 'store/cart.html', {
            'items': items,
            'total': total
        })

    # guest cart
    cart = request.session.get('cart', {})
    items = []
    total = 0

    for pid, qty in cart.items():
        plant = Plant.objects.get(id=pid)
        subtotal = plant.price * qty
        total += subtotal

        items.append({
            'plant': plant,
            'quantity': qty,
            'subtotal': subtotal
        })

    return render(request, 'store/cart.html', {
        'items': items,
        'total': total
    })


# =====================================================
# REMOVE FROM CART
# =====================================================
def remove_from_cart(request, id):

    if request.user.is_authenticated:
        CartItem.objects.filter(user=request.user, plant_id=id).delete()
        return redirect('cart')

    cart = request.session.get('cart', {})
    if str(id) in cart:
        del cart[str(id)]
        request.session['cart'] = cart

    return redirect('cart')


# =====================================================
# CHECKOUT
# =====================================================
@login_required
def checkout(request):

    items = CartItem.objects.filter(user=request.user)
    total = sum(item.subtotal() for item in items)

    if request.method == "POST":

        payment_method = request.POST.get("payment_method")

        order = Order.objects.create(
            user=request.user,
            total=total,
            name=request.POST.get('name'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            pincode=request.POST.get('pincode'),
            payment_method=payment_method,
        )
        send_mail(
            subject=f"🌱 Order #{order.id} Confirmed!",
            message=f"""
            Hi {order.name},

Your plant order has been placed successfully 🌿

Order ID: {order.id}
Total: ₹{order.total}

Thank you for shopping with us!
""",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[request.user.email],
        fail_silently=True,
        )
        # COD FLOW
        if payment_method == "COD":
            for item in items:
                plant = item.plant
                qty = item.quantity

                OrderItem.objects.create(
                    order=order,
                    plant=plant,
                    quantity=qty,
                    price=plant.price
                )

                plant.stock -= qty
                if plant.stock <= 0:
                    plant.stock = 0
                    plant.available = False
                plant.save()

            items.delete()
            return redirect('order_success', order_id=order.id)

        # ONLINE PAYMENT FLOW
        return redirect('payment_page', order_id=order.id)

    return render(request, 'store/checkout.html', {
        'items': items,
        'total': total
    })


# =====================================================
# PAYMENT PAGE (DEMO)
# =====================================================
@login_required
def payment_page(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)

    if request.method == "POST":
        items = CartItem.objects.filter(user=request.user)

        for item in items:
            plant = item.plant
            qty = item.quantity

            OrderItem.objects.create(
                order=order,
                plant=plant,
                quantity=qty,
                price=plant.price
            )

            plant.stock -= qty
            if plant.stock <= 0:
                plant.stock = 0
                plant.available = False
            plant.save()

        items.delete()
        return redirect('order_success', order_id=order.id)

    return render(request, "store/payment.html", {"order": order})


# =====================================================
# ORDER SUCCESS
# =====================================================
@login_required
def order_success(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)
    send_mail(
    subject="Order Confirmed 🌱",
    message=f"Hi {request.user.username}, your order #{order.id} has been placed successfully!",
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=[request.user.email],
    fail_silently=True,
)

    return render(request, 'store/order_success.html', {'order': order})


# =====================================================
# MY ORDERS
# =====================================================
@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/my_orders.html', {'orders': orders})


# =====================================================
# ORDER DETAIL
# =====================================================
@login_required
def order_detail(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)
    items = OrderItem.objects.filter(order=order)

    return render(request, 'store/order_detail.html', {
        'order': order,
        'items': items
    })


# =====================================================
# REGISTER PAGE
# =====================================================
from django.contrib.auth.models import User
from django.contrib.auth import login

def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("register")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        login(request, user)
        messages.success(request, "Account created successfully 🎉")
        return redirect("plant_list")

    return render(request, "store/register.html")

