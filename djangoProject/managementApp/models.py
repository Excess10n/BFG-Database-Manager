from django.db import models
from django.core.validators import MaxValueValidator
from django.contrib.auth.models import User

# Create your models here.

class Member(models.Model):
    firstname = models.CharField(max_length=20, null=False, blank=False)
    surname = models.CharField(max_length=20, null=False, blank=False)
    fullName = models.CharField(max_length=196)
    initials = models.CharField(max_length=10)
    dateUpdated = models.DateField()
    isDeleted = models.BooleanField(default=False)
    profile = models.OneToOneField(User, related_name="user_profile", on_delete=models.CASCADE, null=True, blank=True)
    def __str__(self):
        return self.fullName
    
    def save(self, *args, **kwargs):
        self.fullName = f"{self.surname}, {self.firstname}"
        super(Member, self).save(*args, **kwargs)
    
    class Meta:
        permissions = [
            ("manager", "full db management access"),
            ("member", "access to view db")
        ]

class MemberLogin(models.Model):
    username = models.CharField(max_length=64)

class Genus(models.Model):
    name = models.CharField(max_length=64, null=False, blank=False)
    meaning = models.CharField(max_length=512, null=False, blank=False)
    def __str__(self):
        return self.name

class Group(models.Model):
    name = models.CharField(max_length=64, null=False, blank=False)
    repName = models.CharField(max_length=64, null=False, blank=False)
    repNameSort = models.IntegerField(validators=[MaxValueValidator(10)], null=True)
    dateUpdated = models.DateField()
    def __str__(self):
        return self.name

class Fungi(models.Model):
    fullName = models.CharField(max_length=196, unique=True)
    englishName = models.CharField(max_length=128)
    currentName = models.ForeignKey('FungiCurrent', on_delete=models.CASCADE, related_name='Fungi_current', null=True)
    author = models.CharField(max_length=128)
    group = models.CharField(max_length=64)
    taxonGroup = models.CharField(max_length=64)
    currentTVK = models.CharField(max_length=64)
    remarks = models.TextField()
    dateUpdated = models.DateField()
    creatorFK = models.ForeignKey(Member, on_delete=models.RESTRICT, null=False, related_name='Fungi_creator')
    updaterFK = models.ForeignKey(Member, on_delete=models.RESTRICT, null=False, related_name='Fungi_updater')

    def __str__(self):
        return self.fullName

class FungiCurrent(models.Model):
    currentFungus = models.OneToOneField(Fungi, on_delete=models.CASCADE, null=False)
    def __str__(self):
        return self.currentFungus.fullName

class FungiArchive(models.Model):
    fungiFK = models.OneToOneField(Fungi, on_delete=models.CASCADE)
    uniqueCode = models.CharField(max_length=15, null=False, blank=False, unique=True)
    GBChkLst = models.BooleanField()
    groupOld = models.CharField(max_length=64, null=True)
    interpretCode = models.IntegerField(null=True)
    DJSCode = models.CharField(max_length=10, null=True)
    authority = models.CharField(max_length=128, null=True)
    BAPspecies = models.BooleanField()
    def __str__(self):
        return self.fungiFK

class Site(models.Model):
    name = models.CharField(max_length=64, null=False, blank=False, unique=True)
    gridRef = models.CharField(max_length=20)
    county = models.CharField(max_length=20)
    VC = models.IntegerField(validators=[MaxValueValidator(100)], null=True)
    type = models.CharField(max_length=64)
    remarks = models.TextField()
    dateUpdated = models.DateField(auto_now_add=True)
    creatorFK = models.ForeignKey(Member, on_delete=models.RESTRICT, null=False, related_name='Site_creator')
    updaterFK = models.ForeignKey(Member, on_delete=models.RESTRICT, null=False, related_name='Site_updater')

    class Meta:
        indexes = [
            models.Index(fields=['VC']),
        ]

    def __str__(self):
        return self.name

class Substrate(models.Model):
    name = models.CharField(max_length=64, null=False, blank=False)
    def __str__(self):
        return self.name

class Association(models.Model):
    name = models.CharField(max_length=64, null=False, blank=False)
    latin = models.CharField(max_length=64, null=True, blank=True)
    def __str__(self):
        return self.name

class Record(models.Model):
    class First(models.TextChoices):
        SITE = 'S'
        BUCKS = 'B'
        DATABASE = 'D'
        NONE = 'N'
    
    class Dna(models.TextChoices):
        YES = 'Yes'
        NO = 'No'
        PENDING = 'Pending'

    class Certain(models.TextChoices):
        CERTAIN = 'Certain'
        LIKELY = 'Likely'
        UNCERTAIN = 'Uncertain'

    uniqueCode = models.CharField(max_length=15, null=False, blank=False, unique=True)
    fungusFK = models.ForeignKey(FungiCurrent, on_delete=models.RESTRICT, null=False)
    siteFK = models.ForeignKey(Site, on_delete=models.RESTRICT, null=False)
    recorderFK = models.ForeignKey(Member, on_delete=models.RESTRICT, null=False, related_name='Record_recorder')
    identifierFK = models.ForeignKey(Member, on_delete=models.RESTRICT, null=False, related_name='Record_identifier')
    confirmerFK = models.ForeignKey(Member, on_delete=models.RESTRICT, null=True, related_name='Record_confirmer')
    collectorFK = models.ForeignKey(Member, on_delete=models.RESTRICT, null=False, related_name='Record_collector')
    substrate = models.CharField(max_length=128, null=False, blank=False)
    assoc1  = models.CharField(max_length=128, null=False, blank=True)
    assoc2  = models.CharField(max_length=128, null=False, blank=True)
    assoc3  = models.CharField(max_length=128, null=False, blank=True)
    dateFound = models.DateField()
    dateEntered = models.DateField(auto_now_add=True)
    exported = models.BooleanField(default=False)
    dateExported = models.DateField(null=True)
    remarks = models.TextField(null=True, blank=True)
    dateUpdated = models.DateField()
    updaterFK  = models.ForeignKey(Member, on_delete=models.RESTRICT, null=False, related_name='Record_updater')
    firstRecord = models.CharField(max_length=1, choices=First)
    litRef = models.CharField(max_length=64, null=True, blank=True)
    DNATest = models.CharField(max_length=7, choices=Dna, null=True, blank=True)
    DNAseq = models.TextField(null=True, blank=True)
    image = models.ImageField(null=True, blank=True, upload_to="fungi_photos")
    photographerFK = models.ForeignKey(Member, on_delete=models.RESTRICT, null=True, related_name='Record_photographer')
    certainty = models.CharField(max_length=9, choices=Certain, default="Certain")

    class Meta:
        indexes = [
            models.Index(fields=['dateFound']),
            models.Index(fields=['dateFound', 'siteFK']),
            models.Index(fields=['dateFound', 'recorderFK']),
            models.Index(fields=['fungusFK', 'siteFK']),
            models.Index(fields=['collectorFK', 'dateFound']),
            models.Index(fields=['identifierFK', 'dateFound']),
        ]

    def __str__(self):
        return self.uniqueCode

class RecordArchive(models.Model):
    recFK = models.OneToOneField(Record, on_delete=models.CASCADE)
    repFungus = models.CharField(max_length=15)
    repFungusLocked = models.BooleanField()
    sense = models.CharField(max_length=1, null=True)
    ecoSys = models.CharField(max_length=128, null=True)
    appox = models.BooleanField()
    morph = models.CharField(max_length=64, null=True)
    herbarium = models.CharField(max_length=64, null=True)
    herbRef = models.CharField(max_length=64, null=True)
    photoLoc = models.CharField(max_length=64, null=True)
    BMSDupInd = models.BooleanField()
    BMSHold = models.BooleanField()
    BMSRecNo = models.IntegerField(null=True)
    BMSForay = models.BooleanField()
    BMSMisident = models.BooleanField()
    BMSSenderNo = models.IntegerField(null=True)
    BMSdate = models.DateField(null=True)
    batchRemarks = models.TextField(null=True)
    foray = models.TextField(null=True)
    origin = models.CharField(max_length=64, null=True)
    uniqueFlat = models.CharField(max_length=64, null=True)
    DRecUnique = models.IntegerField(null=True)
    DRecSpecimenNumber = models.CharField(max_length=10, null=True)
    DRecMore = models.CharField(max_length=10, null=True)
    DRecSpecimen = models.CharField(max_length=20, null=True)
    DRecCulture = models.CharField(max_length=20, null=True)
    DRecRecordNumber = models.CharField(max_length=10, null=True)
    DRecRecordedAs = models.CharField(max_length=256, null=True)
    DRec2005 = models.BooleanField()
    RecMsg2 = models.CharField(max_length=32, null=True)
    def __str__(self):
        return self.recFK