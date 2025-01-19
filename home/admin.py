from django.contrib import admin
from home.models import Quiz , Question, Score , StudyMaterial
# Register your models here.
admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Score)
admin.site.register(StudyMaterial)