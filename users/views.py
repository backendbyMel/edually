from django.shortcuts import render

# Create your views here.
def register(request):
    form = UserCreationForm()
    return render(request, 'users/register.html', {'forms:forms'})