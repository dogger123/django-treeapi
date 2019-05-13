from django.contrib import admin

from trees.models import DataSet,Trees,Analysis

# Register your models here.

class DataSetAdmin(admin.ModelAdmin):
    list_display = ["dataSet_id","dataSet_name","table_name","size","create_time"]


class TreeAdmin(admin.ModelAdmin):
    list_display = ["tree_id","tree_name","tree_dict","detpth","nodes_num","create_time"]


class AnalysisAdmin(admin.ModelAdmin):
    list_display = ["analysis_id","analysis_name","accuracy","ifthen","content","create_time"]

admin.site.register(DataSet,DataSetAdmin)
admin.site.register(Trees,TreeAdmin)
admin.site.register(Analysis,AnalysisAdmin)
