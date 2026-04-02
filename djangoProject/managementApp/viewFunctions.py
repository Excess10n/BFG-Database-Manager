from .models import Fungi, FungiCurrent

def getFungiObjects(name): # returns (currentFungi, parent, child (None if not a child))
    fungus = Fungi.objects.get(fullName=name)
    current = FungiCurrent.objects.filter(currentFungus=fungus)
    if current.count() == 1:
        return current.first(), fungus, None
    return fungus.currentName, fungus.currentName.currentFungus, fungus
    