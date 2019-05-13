import sys
import os
import json
import traceback
from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse,JsonResponse
from . import models

#rest_framework
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from trees.utils.serializers import DataSetSerializer
from trees.utils.serializers import TreeSerializer
from trees.utils.serializers import AnalysisSerializer

def index(request, tree_id):
    pass


def upload(request):
    return render(request, 'upload.html')


def dataSet(request, dataset_id):
    if request.method == "GET":
        try:
            if dataset_id == '':
                dataSet = models.DataSet.objects.all()
                serializer = DataSetSerializer(dataSet, many=True)
            else:
                dataSet = models.DataSet.objects.get(pk=dataset_id)
                serializer = DataSetSerializer(dataSet)
        except:
            return JsonResponse({'message': 'DataSet Object not found'}, status=404)
        return JsonResponse(serializer.data, safe=False)
    elif request.method == "PUT":
        data = JSONParser().parse(request)
        dataSet = None
        serializer = DataSetSerializer(dataSet, data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors, status=400)
    elif request.method == "POST":
        dataSet_name = request.POST.get('dataSet_name', 'dataset')
        print(dataSet_name)
        dataSet_type = request.POST.get('dataSet_type', 'trainset')
        print(dataSet_type)
        myFile = request.FILES.get('csvdataset')
        if not myFile:
            return HttpResponse("no files uploaded!")
        else:
            destination = open(os.path.join('trees/upload', myFile.name), 'wb')
            for chunk in myFile.chunks():
                destination.write(chunk)
            destination.close()

            # 开始调用模块转移数据到数据库
            from trees.utils import csvimport
            table_name, size = csvimport.writeToDB('trees/upload/', myFile.name)
            print(table_name, "|", size)
            newdataSet = models.DataSet(dataSet_name=dataSet_name, dataSet_type="trainset", table_name=table_name,
                                        size=size)
            newdataSet.save()
            return JsonResponse(DataSetSerializer(newdataSet).data)
            # # 为tree发送POST请求
            # tree_name = myFile.name
            # dataSet_id = newdataSet.dataSet_id
            # print(dataSet_id)
            # # 根据所传入的树类型,训练集创建树
            # # 先获取数据集的表名
            # try:
            #     dataSet = models.DataSet.objects.get(pk=dataSet_id)
            # except:
            #     return JsonResponse({'message': 'dataset not found'}, status=404)
            # # 调入ID3的模块
            # from trees.utils import ID3_Standard
            # ID3_controller = ID3_Standard.ID3('db', dataSet.table_name,
            #                                      fields=['四级', '六级','政治面貌','计算机等级','综合能力','性别','result'])
            # jsonTree = ID3_controller.GenerateID3('json')
            #
            # tree_dict = jsonTree
            # nodes_num,detpth = ID3_controller.calcProperties()
            #
            # newTree = models.Trees(tree_name=tree_name, tree_dict=tree_dict, detpth=detpth, nodes_num=nodes_num,
            #                       dataSet_id=dataSet_id)
            # newTree.save()
            # # 返回新创建对象的序列化JSON
            # return JsonResponse(TreeSerializer(newTree).data)
    elif request.method == 'DELETE':
        try:
            dataSet = models.DataSet.objects.get(pk=dataset_id)
        except:
            return JsonResponse({'message': 'DataSet Object not found'}, status=404)
        dataSet.delete()
        return JsonResponse({'message': 'delete success'}, status=200)
    else:
        return JsonResponse({'message': 'unsuported method', 'method': request.method})


# 对决策树的操作
def tree(request, tree_id):
    # GET请求用于获取tree
    if request.method == "GET":
        try:
            if tree_id == '':
                tree = models.Trees.objects.all()
                print(tree)
                serializer = TreeSerializer(tree, many=True)
            else:
                tree = models.Trees.objects.get(pk=tree_id)
                serializer = TreeSerializer(tree)
        except:
            return JsonResponse({'message': 'Tree Object not found'}, status=404)
        return JsonResponse(serializer.data, safe=False)
    # PUT请求用于客户端生成好的tree直接插入数据库
    elif request.method == "PUT":
        data = JSONParser().parse(request)
        tree = None
        serializer = TreeSerializer(tree, data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors, status=400)
    # POST请求用于客户端传入训练集和类型在服务器端训练再插入数据库
    elif request.method == "POST":
        # defautDict = '{"name": "cpp", "text": "null", "children": [{"name": "pass", "text": ">77.0", "children": "null"}, {"name": "failed", "text": "<=77.0", "children": "null"}]}'
        # print(request.POST.get('tree'))
        dicttree = json.loads(request.POST.get('tree'))
        tree_name = dicttree['tree_name']
        tree_type = dicttree['tree_type']
        dataSet_id = dicttree['dataSet_id']
        print(dataSet_id)
        # 根据所传入的树类型,训练集创建树
        # 先获取数据集的表名
        try:
            dataSet = models.DataSet.objects.get(pk=dataSet_id)
        except:
            return JsonResponse({'message': 'dataset not found'}, status=404)
        # 调入ID3和C4.5模块
        if tree_type == 'ID3':
            from trees.utils import ID3_Standard
            try:
                ID3_controller = ID3_Standard.ID3('db', dataSet.table_name,
                                                  fields=['四级', '六级', '政治面貌', '计算机等级', '综合能力', '性别', 'result'])
                jsonTree = ID3_controller.GenerateID3('json')
                nodes_num, detpth = ID3_controller.calcProperties()
            except:
                traceback.print_stack()
                return JsonResponse({'message': 'can not build tree'})

        elif tree_type == 'C45':
            from trees.utils import C45
            # try:
                # 注意 C45未开发数据库读取接口
                # C45_controller = C45.C45('db', dataSet.table_name,
                #                                   )
                # jsonTree = C45_controller.GenerateC45('json')
                # from trees.utils import C45
                # 注意 C45未开发数据库读取接口
            C45_controller = C45.C45('db', 'subtreeapi.' + dataSet.table_name, fields=['四级', '六级', '政治面貌', '计算机等级', '综合能力', '性别', 'result'])
            jsonTree = C45_controller.GenerateC45('json')
            data_type,nodes_num, detpth = C45_controller.CalcProperties()
            # except:
            #     traceback.print_stack()
            #     return JsonResponse({'message': 'can not build tree'})


        tree_dict = jsonTree

        newTree = models.Trees(tree_name=tree_name, tree_dict=tree_dict, detpth=detpth, nodes_num=nodes_num, dataSet_id=dataSet_id,tree_type=tree_type)
        # print(newTree)
        newTree.save()
        # 返回新创建对象的序列化JSON
        return JsonResponse(TreeSerializer(newTree).data)

    elif request.method == 'DELETE':
        try:
            tree = models.Tree.objects.get(pk=tree_id)
        except:
            return JsonResponse({'message': 'Tree Object not found'}, status=404)
        tree.delete()
        return JsonResponse({'message': 'delete success'}, status=200)
    else:
        return JsonResponse({'message': 'unsuported method', 'method': request.method})


def analysis(request, analysis_id):
    if request.method == "GET":
        try:
            if analysis_id == '':
                analysis = models.Analysis.objects.all()
                serializer = AnalysisSerializer(analysis, many=True)
            else:
                analysis = models.Analysis.objects.get(pk=analysis_id)
                serializer = AnalysisSerializer(analysis)
        except:
            return JsonResponse({'message': 'Analysis Object not found'}, status=404)
        return JsonResponse(serializer.data, safe=False)
    elif request.method == "PUT":
        data = JSONParser().parse(request)
        analysis = None
        serializer = AnalysisSerializer(analysis, data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors, status=400)
    elif request.method == 'DELETE':
        try:
            analysis = models.Analysis.objects.get(pk=analysis_id)
        except:
            return JsonResponse({'message': 'Analysis Object not found'}, status=404)
        analysis.delete()
        return JsonResponse({'message': 'delete success'}, status=200)
    else:
        return JsonResponse({'message': 'unsuported method', 'method': request.method})


def drawTree(request):
    if request.method == "GET":
        jsoncontent = json.dumps(request.GET.get('json'))
        print(json)
        context = {'jsonContent': jsoncontent}
        return render(request, 'index.html', context)
    elif request.method == "POST":
        jsoncontent = request.POST['json']
        print(json)
        context = {'jsonContent': jsoncontent}
        return render(request, 'index.html', context)
    else:
        return HttpResponse('{"code":102,"message":"不支持get请求，请使用post请求"}')

# class UserForm(forms.Form):
#     headImg = forms.FileField()
#
# # 获得所有的决策树
# def getAllTrees(request):
#     all_entries = Tree.objects.all().order_by("id")
#     arrayList = []
#     for item in all_entries:
#         arrayList.append({
#             "id": item.id,
#         })
#     return HttpResponse(json.dumps(arrayList))

def condForecast(request):
    if request.method == "POST":
        sex = request.POST.get('sex')
        cet4 = request.POST.get('cet4')
        cet6 = request.POST.get('cet6')
        party = request.POST.get('party')
        computer = request.POST.get('computer')
        rank = request.POST.get('rank')
        id = request.POST.get('tree_id')
        type = request.POST.get('type')
        # print(id)
        tup = (cet4,cet6,party,computer,rank,sex)
        list2 = []
        list2 = list(tup)
        # print(list2)
        if type == "ID3":
            from trees.utils import ID3_Standard
            if id == '':
                id == 1
            tree = models.Trees.objects.get(tree_id=id)
            jsontree2 = json.loads(tree.tree_dict)
            # print(jsontree2)
            # jsontree = {"name": "\u653f\u6cbb\u9762\u8c8c", "col": 2, "text": "text", "children": [{"name": "\u7efc\u5408\u80fd\u529b", "col": 3, "text": "member", "children": [{"name": "\u8ba1\u7b97\u673a\u7b49\u7ea7", "col": 2, "text": "3", "children": [{"name": "\u79c1\u4f01", "col": "null", "text": "3", "children": "null"}, {"name": "\u56fd\u4f01", "col": "null", "text": "2", "children": "null"}, {"name": "\u5347\u5b66", "col": "null", "text": "1", "children": "null"}]}, {"name": "\u56db\u7ea7", "col": 0, "text": "2", "children": [{"name": "\u8ba1\u7b97\u673a\u7b49\u7ea7", "col": 1, "text": "no", "children": [{"name": "\u79c1\u4f01", "col": "null", "text": "4", "children": "null"}, {"name": "\u5347\u5b66", "col": "null", "text": "2", "children": "null"}, {"name": "\u79c1\u4f01", "col": "null", "text": "1", "children": "null"}]}, {"name": "\u79c1\u4f01", "col": "null", "text": "pass", "children": "null"}]}, {"name": "\u8ba1\u7b97\u673a\u7b49\u7ea7", "col": 2, "text": "1", "children": [{"name": "\u516d\u7ea7", "col": 1, "text": "3", "children": [{"name": "\u5347\u5b66", "col": "null", "text": "no", "children": "null"}, {"name": "\u79c1\u4f01", "col": "null", "text": "pass", "children": "null"}]}, {"name": "\u79c1\u4f01", "col": "null", "text": "2", "children": "null"}, {"name": "\u56db\u7ea7", "col": 0, "text": "1", "children": [{"name": "\u56fd\u4f01", "col": "null", "text": "no", "children": "null"}, {"name": "\u5347\u5b66", "col": "null", "text": "pass", "children": "null"}]}]}]}, {"name": "\u5347\u5b66", "col": "null", "text": "party", "children": "null"}]}
            labels =['四级', '六级','政治面貌','计算机等级','综合能力','性别']
            result = ID3_Standard.classify(jsontree2,labels,list2)
            # print(ID3_result)
            # observation.append(sex)
        elif type == "C45":
            from trees.utils import C45
            if id == '':
                id == 1
            tree = models.Trees.objects.get(tree_id=id)
            jsontree2 = json.loads(tree.tree_dict)
            labels = ['四级', '六级', '政治面貌', '计算机等级', '综合能力', '性别']
            result = C45.classify(jsontree2, labels, list2, "Discrete")
    return HttpResponse(result)

def getAdvise(request):
    if request.method == "POST":
        result = request.POST.get('result')
        print(result)
        if result == '升学':
            return HttpResponse("如果有升学的打算，那么对计算机专业基础知识的掌握显得尤为的关键，同样的要丰富自己的竞赛经历，当然，在基础学科的复试过程中，吃苦耐劳的精神也是必不可少的。")
        elif result == '私企':
            return HttpResponse("若要提高自己在私企的就业层次，需着重加强计算机水平能力的提高，而沟通能力的培养也需要加以重视。随着私企间竞争的加剧，具有优秀的编码能力和自我学习能力等综合素质能力强的学生需求越来越强烈；")
        elif result == '国企':
            return HttpResponse("国企在我国的社会经济中占主导地位，要求学生具有过硬的专业的知识，理论指导实践的水平高，具有相关的实践经验，从事的领域上手快，学习能力强。另外，政治面貌和思想觉悟也是不可忽视的重要因素")