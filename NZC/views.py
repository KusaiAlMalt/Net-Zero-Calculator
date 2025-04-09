from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def pdf(request):
    return render(request, 'pdf.html')

def manual(request):
    return render(request, 'manual.html')

def results(request):
    if request.method == 'POST' and request.FILES.get('file'):   
        results = f"you uploaded {request.FILES.get('file')}, and you should reduce your carbon footprint by x and y"
        context = {
            'results': results
        }
    elif request.method == 'POST' and request.POST.get('scope1') and request.POST.get('scope2') and request.POST.get('scope3') and request.POST.get('profit'):
        results = f"you selected {request.POST.get('scope1')} and {request.POST.get('scope2')} and {request.POST.get('scope3')} and profit {request.POST.get('profit')}, and you should reduce your carbon footprint by x and y"
        context = {
            'results': results
        }
    else:
        results = "Please upload a file or select a scope."
        context = {
            'results': results
        }
    return render(request, 'results.html', context)
