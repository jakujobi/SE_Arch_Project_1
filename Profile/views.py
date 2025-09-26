from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.contrib import messages
from logging import getLogger  

from Profile.models import Payment, Subscription  # Add this import
from .forms import ProfileForm, CustomUserCreationForm  # Import the ProfileForm and CustomUserCreationForm
from datetime import timedelta, date  # Add this import

logger = getLogger(__name__)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # The email is already handled in the form's save method
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('home')
        # If form is invalid, render the form with errors
        return render(request, 'register.html', {'form': form})
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    error_message = None
    username = None

    # Display success or error messages from other views
    storage = messages.get_messages(request)
    storage.used = True  # Mark messages as used to clear them # type: ignore

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        username = request.POST.get('username', '')  # Preserve the username
        if form.is_valid():
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home') 
        
        # Create a custom error message based username and password validity     
        error_message = "Invalid login credentials."
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form, 'error_message': error_message, 'username': username})

@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

# Profile; Also has subscription status and payment form
@login_required
def profile(request):
    subscription_string = ""

    # Retrieve the logged-in user's profile
    user_profile = request.user.profile

    if not Subscription.objects.filter(user_id=user_profile, start_date__lte=now(), end_date__gte=now()).exists():
        entry = None
        subscription_string = "Not currently subscribed"
    else:
        entry = Subscription.objects.filter(user_id=user_profile, start_date__lte=now(), end_date__gte=now()).get()
        subscription_string = "Subscribed until " + entry.end_date.strftime("%Y-%m-%d")
    
    return render(request, 'profile.html', {
            'subscription_string': subscription_string,
        })

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            profile = form.save(commit=False)
            # Update data in the User model
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.username = form.cleaned_data['username']
            request.user.email = form.cleaned_data['email']
            request.user.save()
            profile.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user.profile, initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'username': request.user.username
        })
    return render(request, 'edit_profile.html', {
        'form': form,
    })

@login_required
def payment(request):
    PRICE_PER_DAY = 1.00

    subscription_string = ""
    form_data = {}
    total_price = 0.0

    # Retrieve the logged-in user's profile
    user_profile = request.user.profile
    
    # Check if User is subscribed
    if not Subscription.objects.filter(user_id=user_profile, start_date__lte=now(), end_date__gte=now()).exists():
        entry = None
        subscription_string = "You are currently not subscribed"
    else:
        entry = Subscription.objects.filter(user_id=user_profile, start_date__lte=now(), end_date__gte=now()).get()
        subscription_string = "You are subscribed until: " + entry.end_date.strftime("%Y-%m-%d")

    if request.method == 'POST':
        if request.POST['action'] == 'purchase':
            subscription_days = int(request.POST.get('subscription_days'))
            card_number = str(request.POST.get('card_number'))
            expiration_date = request.POST.get('expiration_date')
            security_code = int(request.POST.get('security_code'))
            country = str(request.POST.get('country'))
            zip_code = int(request.POST.get('zip_code'))

            form_data = {
                "subscription_days": subscription_days,
                "card_number": card_number,
                "expiration_date": expiration_date,
                "security_code": security_code,
                "country": country,
                "zip_code": zip_code
            }

            if entry is not None:
                entry.end_date = entry.end_date + timedelta(days=subscription_days)
                entry.save()
            else:
                new_subscription = Subscription(
                    user_id = user_profile,
                    tier = "Premium",
                    start_date = date.today(),
                    end_date = date.today() + timedelta(days=subscription_days),
                )
                new_subscription.save()
                entry = new_subscription

            total_price = PRICE_PER_DAY * subscription_days

            new_payment = Payment(
                user_id = user_profile,
                amount = total_price,
                payment_method = "Credit Card",
                payment_date = date.today(),
                transaction_id = entry.pk,
                payment_status = "PID"
            )
            new_payment.save()

            # Redirect to prevent duplicate POST requests from making multiple db entries
            return redirect('payment')

    # Shows payment methods and allows to add new ones
    return render(request, 'payment.html', {
        'subscription_string': subscription_string,
        'form_data': form_data,
        'total_price': total_price
    })