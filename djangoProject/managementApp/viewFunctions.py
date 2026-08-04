from .models import Fungi, FungiCurrent

def getFungiObjects(name): # returns (currentFungi, parent, child (None if not a child))
    try:
        fungus = Fungi.objects.get(fullName=name)
    except:
        return None, None, None
    current = FungiCurrent.objects.filter(currentFungus=fungus)
    if current.count() == 1:
        return current.first(), fungus, None
    return fungus.currentName, fungus.currentName.currentFungus, fungus

def getAllCurrentFungiObjects():
    return Fungi.objects.filter(currentName=None)