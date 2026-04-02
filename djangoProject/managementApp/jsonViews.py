from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import Fungi, Record, Site
import datetime

@require_GET
def fungiSuggestions(request):
    q = request.GET.get("q")
    date = request.GET.get("date")
    site = request.GET.get("site")
    results = []
    if q:
        results = list(Fungi.objects.filter(fullName__icontains=q).values_list("fullName", flat=True))
    
    dup = "false"
    if date != None and site != None:
        fungus = Fungi.objects.filter(fullName=q)
        if fungus.count() == 1:
            date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
            rec = Record.objects.filter(fungusFK=fungus.first(), siteFK=Site.objects.get(id=site), dateFound=date)
            
            if rec.count() > 0:
                dup = "true"

    return JsonResponse({"results": results, "dup": dup})
