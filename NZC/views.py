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
    if request.method == 'POST' and request.FILES['file']:   
        results = f"you uploaded {request.FILES.get('file')}, and you should reduce your carbon footprint by x and y"
        context = {
            'results': results,
        }
    else:
        context = {
            'results': None,
        }
    return render(request, 'results.html', context)
