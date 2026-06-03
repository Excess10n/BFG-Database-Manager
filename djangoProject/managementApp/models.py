from django.db import models
from django.core.validators import MaxValueValidator
from django.contrib.auth.models import User

# Create your models here.

class Member(models.Model):
    firstname = models.CharField(max_length=20, null=False, blank=False)
    surname = models.CharField(max_length=20, null=False, blank=False)
    initials = models.CharField(max_length=5, null=False, blank=False, unique=True)
    dateUpdated = models.DateField()
    isDeleted = models.BooleanField(default=False)
    def __str__(self):
        return self.initials

class Manager(models.Model):
    profile = models.OneToOneField(User, related_name="user_profile", on_delete=models.CASCADE)
    member = models.OneToOneField(Member, on_delete=models.CASCADE)

    class Meta:
        permissions = [
            ("manager", "full db management access")
        ]

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
    uniqueCode = models.CharField(max_length=15, null=False, blank=False, unique=True)
    genus = models.CharField(max_length=64)
    species = models.CharField(max_length=64)
    variety = models.CharField(max_length=64)
    group = models.CharField(max_length=64)
    fullName = models.CharField(max_length=196)
    commonName = models.CharField(max_length=128)
    currentName = models.ForeignKey('FungiCurrent', on_delete=models.RESTRICT, related_name='Fungi_current', null=True)
    remarks = models.TextField()
    dateUpdated = models.DateField()
    creatorFK = models.ForeignKey(Member, on_delete=models.RESTRICT, null=False, related_name='Fungi_creator')
    updaterFK = models.ForeignKey(Member, on_delete=models.RESTRICT, null=False, related_name='Fungi_updater')
    # EXTRA
    capRadius = models.FloatField(null=True)
    colourDarkness = models.FloatField(null=True)
    height = models.FloatField(null=True)
    centroid = models.IntegerField(default=-1)

    class Meta:
        indexes = [
            models.Index(fields=['centroid']),
        ]

    def __str__(self):
        return self.fullName
    
    def save(self, *args, **kwargs):
        if self.variety == "":
            self.fullName = f"{self.genus} {self.species}"
        else:
            self.fullName = f"{self.genus} {self.species} {self.variety}"
        super(Fungi, self).save(*args, **kwargs)

class FungiCentroids(models.Model):
    capRadius = models.FloatField(null=True)
    colourDarkness = models.FloatField(null=True)
    height = models.FloatField(null=True)

class FungiCurrent(models.Model):
    currentFungus = models.OneToOneField(Fungi, on_delete=models.CASCADE, null=False)
    def __str__(self):
        return self.currentFungus.fullName

class FungiArchive(models.Model):
    fungiFK = models.OneToOneField(Fungi, on_delete=models.CASCADE)
    GBChkLst = models.BooleanField()
    groupOld = models.CharField(max_length=64, null=True)
    interpretCode = models.IntegerField(null=True)
    DJSCode = models.CharField(max_length=10, null=True)
    authority = models.CharField(max_length=128, null=True)
    BAPspecies = models.BooleanField()
    def __str__(self):
        return self.fungiFK

class Site(models.Model):
    name = models.CharField(max_length=16, null=False, blank=False, unique=True)
    reportingName = models.CharField(max_length=64)
    gridRef = models.CharField(max_length=20)
    county = models.CharField(max_length=20)
    VC = models.IntegerField(validators=[MaxValueValidator(100)], null=True)
    country = models.CharField(max_length=20)
    type = models.CharField(max_length=64)
    remarks = models.TextField()
    dateUpdated = models.DateField(auto_now_add=True)
    creatorFK = models.ForeignKey(Member, on_delete=models.RESTRICT, null=False, related_name='Site_creator')
    updaterFK = models.ForeignKey(Member, on_delete=models.RESTRICT, null=False, related_name='Site_updater')
    # EXTRA FEILDS REMOVE LATER
    lat = models.FloatField(default=0.0)
    lon = models.FloatField(default=0.0)
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

    uniqueCode = models.CharField(max_length=15, null=False, blank=False, unique=True)
    fungusFK = models.ForeignKey(FungiCurrent, on_delete=models.RESTRICT, null=False)
    siteFK = models.ForeignKey(Site, on_delete=models.RESTRICT, null=False)
    recorderFK = models.ForeignKey(Member, on_delete=models.RESTRICT, null=False, related_name='Record_recorder')
    identifierFK = models.ForeignKey(Member, on_delete=models.RESTRICT, null=False, related_name='Record_identifier')
    confirmerFK = models.ForeignKey(Member, on_delete=models.RESTRICT, null=True, related_name='Record_confirmer')
    collectorFK = models.ForeignKey(Member, on_delete=models.RESTRICT, null=False, related_name='Record_collector')
    substrFK = models.ForeignKey(Substrate, on_delete=models.RESTRICT, null=False, related_name='Record_substr')
    assoc1FK  = models.ForeignKey(Association, on_delete=models.RESTRICT, null=True, blank=True, related_name='Record_assoc1')
    assoc2FK  = models.ForeignKey(Association, on_delete=models.RESTRICT, null=True, blank=True, related_name='Record_assoc2')
    assoc3FK  = models.ForeignKey(Association, on_delete=models.RESTRICT, null=True, blank=True, related_name='Record_assoc3')
    dateFound = models.DateField()
    dateEntered = models.DateField(auto_now_add=True)
    sentBMS = models.BooleanField(default=False)
    dateSentBMS = models.DateField(null=True)
    remarks = models.TextField(null=True, blank=True)
    dateUpdated = models.DateField()
    updaterFK  = models.ForeignKey(Member, on_delete=models.RESTRICT, null=False, related_name='Record_updater')
    firstRecord = models.CharField(max_length=1, choices=First)
    litRef = models.CharField(max_length=64, null=True, blank=True)
    DNATest = models.BooleanField(null=True)
    image = models.ImageField(null=True, blank=True)
    knownDup = models.BooleanField(default=False)
    # EXTRA FEILDS REMOVE LATER
    lat = models.FloatField(default=0.0)
    lon = models.FloatField(default=0.0)
    dayOfYear = models.IntegerField(default=-1000)
    def __str__(self):
        return self.uniqueCode
    
    def save(self, *args, **kwargs):
        self.dayOfYear = self.dateFound.timetuple().tm_yday
        super(Record, self).save(*args, **kwargs)
    
    class Meta:
        indexes = [
            models.Index(fields=['-dateFound', 'dayOfYear']),
        ]

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