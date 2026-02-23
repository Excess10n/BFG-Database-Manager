from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import Fungi

@require_GET
def fungiSuggestions(request):
    q = request.GET.get("q")
    results = []
    if q:
        results = list(Fungi.objects.filter(fullName__icontains=q).values_list("fullName", flat=True))

    return JsonResponse({"results": results})
