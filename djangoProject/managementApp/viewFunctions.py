from .models import Fungi, FungiCurrent

def getFungiObjects(name): # returns (currentFungi, parent, array of children)
    try:
        fungus = Fungi.objects.get(fullName=name)
    except:
        return None, None, None
    current = FungiCurrent.objects.filter(currentFungus=fungus)
    if current.count() == 1:
        children = Fungi.objects.filter(currentName=current.first())
        return current.first(), fungus, children
    return fungus.currentName, fungus.currentName.currentFungus, [fungus]

def createNewCurrentFungi(id):
    curr = FungiCurrent(currentFungus=Fungi.objects.get(id=id))
    curr.save()
    return curr