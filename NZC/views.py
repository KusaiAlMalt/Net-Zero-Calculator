from django.shortcuts import render, redirect
from django.contrib import messages
from calculator1 import *
from .pdf_analyzer import extract_info_from_pdf
import math


# Create your views here.
def index(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def pdf(request):
    return render(request, 'pdf.html')

def manual(request):
    return render(request, 'manual.html', {"scopes" : [1,2,3]})

def supplier_map(request):
    return render(request, 'map.html')

def results(request):
    context = {}  # Initialize context as empty dictionary
    
    # Exempel på kostnadsintervall (du kan lägga till fler eller ändra)
    removal_methods = {
        'Direct Air Capture': (100, 345),      # Cost in U.S. dollars per ton of CO₂
        'Biochar': (10, 345),
        'Reforestation': (5, 240),
        'Enhanced Weathering': (50, 200),
        'BECCS': (15, 400),
        'Soil carbon sequestration': (45, 100)
    }
    
    if request.method == 'POST':
        if request.FILES.get('file'):
            pdf_file = request.FILES.get('file')

            if not pdf_file.name.endswith('.pdf'):
                messages.error(request, 'File is not PDF type')
                return redirect('index')

            try:
                # Use the PDF analyzer to get initial data
                analysis_results = extract_info_from_pdf(pdf_file)
                extracted_values = analysis_results['extracted_values']
                
                # Sätt defaultvärden till '-' om de saknas
                data = {
                    'scope1': extracted_values.get('scope1', '-'),
                    'scope2': extracted_values.get('scope2', '-'),
                    'scope3': extracted_values.get('scope3', '-'),
                    'profit': extracted_values.get('profit', '-')
                }

                # Om alla scope-värden är siffror, kör beräkning och visa tabell
                if all(isinstance(data[k], int) or (isinstance(data[k], str) and data[k].isdigit()) for k in ['scope1', 'scope2', 'scope3']):
                    # Konvertera strängar till int om det behövs
                    for k in ['scope1', 'scope2', 'scope3']:
                        if isinstance(data[k], str):
                            data[k] = int(data[k])
                    # profit kan vara '-' så vi hanterar den separat
                    if isinstance(data['profit'], str) and data['profit'].isdigit():
                        data['profit'] = int(data['profit'])
                    results = get_results(data)

                    # Beräkna kostnader per metod
                    costs_per_method = {}
                    price_per_ton = {}
                    for method, (low, high) in removal_methods.items():
                        costs_per_method[method] = {
                            'scope1': (math.ceil(data['scope1'] * low * 10 / 1_000), math.ceil(data['scope1'] * high * 10 / 1_000)),
                            'scope2': (math.ceil(data['scope2'] * low * 10 / 1_000), math.ceil(data['scope2'] * high * 10 / 1_000)),
                            'scope3': (math.ceil(data['scope3'] * low * 10 / 1_000), math.ceil(data['scope3'] * high * 10 / 1_000)),
                            'total': (math.ceil((data['scope1'] + data['scope2'] + data['scope3']) * low * 10 / 1_000),
                                      math.ceil((data['scope1'] + data['scope2'] + data['scope3']) * high * 10 / 1_000))
                        }
                        price_per_ton[method] = (low * 10, high * 10)  # SEK per ton
                    context = {
                        'results': results,
                        'text_sample': analysis_results['text_sample'],
                        'relevant_contexts': analysis_results['relevant_contexts'],
                        'costs_per_method': costs_per_method,
                        'price_per_ton': price_per_ton
                    }
                else:
                    results = (
                        f"Scope 1: {data['scope1']}\n"
                        f"Scope 2: {data['scope2']}\n"
                        f"Scope 3: {data['scope3']}\n"
                        f"Vinst (MSEK): {data['profit']}"
                    )
                    context = {
                        'results': results,
                        'text_sample': analysis_results['text_sample'],
                        'relevant_contexts': analysis_results['relevant_contexts']
                    }
            except Exception as e:
                messages.error(request, f'Error analyzing PDF: {str(e)}')
                return redirect('index')

        elif request.POST.get('scope1') and request.POST.get('scope2') and request.POST.get('scope3') and request.POST.get('profit'):
            data = {
                'scope1': int(request.POST.get('scope1')), 
                'scope2': int(request.POST.get('scope2')), 
                'scope3': int(request.POST.get('scope3')),
                'profit': int(request.POST.get('profit'))
            }
            results = get_results(data)
            context = {
                'results': results
            }

            # Beräkna kostnader per metod
            costs_per_method = {}
            price_per_ton = {}
            for method, (low, high) in removal_methods.items():
                costs_per_method[method] = {
                    'scope1': (math.ceil(data['scope1'] * low * 10 / 1_000), math.ceil(data['scope1'] * high * 10 / 1_000)),
                    'scope2': (math.ceil(data['scope2'] * low * 10 / 1_000), math.ceil(data['scope2'] * high * 10 / 1_000)),
                    'scope3': (math.ceil(data['scope3'] * low * 10 / 1_000), math.ceil(data['scope3'] * high * 10 / 1_000)),
                    'total': (math.ceil((data['scope1'] + data['scope2'] + data['scope3']) * low * 10 / 1_000),
                              math.ceil((data['scope1'] + data['scope2'] + data['scope3']) * high * 10 / 1_000))
                }
                price_per_ton[method] = (low * 10, high * 10)  # SEK per ton
            context['costs_per_method'] = costs_per_method
            context['price_per_ton'] = price_per_ton
        else:
            messages.error(request, 'Missing required data')
            return redirect('index')
    else:
        messages.error(request, 'Please submit data first')
        return redirect('index')
        
    return render(request, 'results.html', context)
