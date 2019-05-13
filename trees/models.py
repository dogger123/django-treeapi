from django.db import models
from django.utils import timezone


class DataSet(models.Model):
    dataSet_id = models.AutoField(primary_key=True)
    dataSet_name = models.CharField(max_length=200,null=True)
    dataSet_type = models.CharField(max_length=200,null=True)
    table_name = models.CharField(max_length=200,null=True)
    size = models.IntegerField(default=0)
    create_time = models.DateTimeField('cretetime', default=timezone.now)


class Trees(models.Model):
    tree_id = models.AutoField(primary_key=True)
    # dataSet_id = models.IntegerField(blank=False,null=False)
    dataSet = models.ForeignKey(DataSet, on_delete=models.PROTECT)
    tree_name = models.CharField(max_length=200,default=0)
    tree_type = models.CharField(max_length=200,null=True)
    tree_dict = models.TextField(default=0)
    detpth = models.IntegerField(default=0)
    nodes_num = models.IntegerField(default=0)
    create_time = models.DateTimeField('cretetime', default=timezone.now)


class Analysis(models.Model):
    analysis_id = models.AutoField(primary_key=True)
    tree = models.ForeignKey(Trees, on_delete=models.PROTECT)
    dataSet = models.ForeignKey(DataSet, on_delete=models.PROTECT)
    analysis_name = models.CharField(max_length=200)
    accuracy = models.FloatField()
    ifthen = models.TextField()
    content = models.TextField(null=True)
    create_time = models.DateTimeField('cretetime', default=timezone.now)


# 导入的数据集文件
# class User(models.Model):
#     headImg = models.FileField(upload_to = './upload/')
#
