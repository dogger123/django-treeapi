from rest_framework import serializers
from trees.models import DataSet
from trees.models import Trees
from trees.models import Analysis

class DataSetSerializer(serializers.Serializer):
    dataSet_id = serializers.IntegerField(read_only=True)
    dataSet_name = serializers.CharField(required=True, allow_blank=False, max_length=200)
    dataSet_type = serializers.CharField(required=True, allow_blank=False, max_length=200)
    table_name = serializers.CharField(required=True, allow_blank=False)
    size = serializers.IntegerField(required=True)
    create_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')

    def create(self, validated_data):
        return DataSet.objects.create(**validated_data)

class TreeSerializer(serializers.Serializer):
    tree_id = serializers.IntegerField(read_only=True)
    tree_name = serializers.CharField(required=True, allow_blank=False, max_length=200)
    tree_dict = serializers.CharField(required=True, allow_blank=False)
    tree_type = serializers.CharField(required=True, allow_blank=False)
    detpth = serializers.IntegerField(required=True)
    nodes_num = serializers.IntegerField(required=True)
    create_time = serializers.DateTimeField(read_only=True,format='%Y-%m-%d %H:%M')
    dataSet_id = serializers.IntegerField(required=True)

    def create(self, validated_data):
        return Trees.objects.create(**validated_data)

class AnalysisSerializer(serializers.Serializer):
    analysis_id = serializers.IntegerField(read_only=True)
    analysis_name = serializers.CharField(required=True, allow_blank=False, max_length=200)
    accuracy = serializers.FloatField(required=True)
    ifthen = serializers.CharField(required=True, allow_blank=False)
    content = serializers.CharField(required=False, allow_blank=True)
    create_time = serializers.DateTimeField(read_only=True,format='%Y-%m-%d %H:%M')
    dataSet_id = serializers.IntegerField(required=True)
    tree_id = serializers.IntegerField(required=True)

    def create(self, validated_data):
        return Analysis.objects.create(**validated_data)