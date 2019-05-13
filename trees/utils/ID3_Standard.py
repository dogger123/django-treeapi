import math
import operator
import csv

import pymysql
import json
'''
contents:
    1. 初始化数据集
        createDataSet() => dataSet,labels
        readFromCSV() => datas(orderedDict类型)
        readFromCSVs() => dataSet(二维数组),labels(数组)
    2. 构造
        2.1 计算信息熵
        2.2 按照最大信息增益划分数据集
        2.3 创建决策树
        createTree(dataSet,labels) => tree(字典)
    3. 用于分类
        3.1 直接预测分类
        3.2 文件化便于直接读取进行预测
    4. 图形化
        4.1 使用Matplotlib绘制决策树
'''

#-----------------I. 数据读取------------------------
# I.1 从一个有表头的csv文件读取数据
def readFromCSV(filename='data'):
    f = open(filename+".csv")
    datas = []
    # 开始读取数据集
    for line in f:
        newline = line.strip('\n').split(',')
        # 插入到datas
        datas.append(newline)
    f.close()
    #print(datas)
    labels = datas[0][:len(datas[1])-1] #这里根据第2行的数据列数来决定labels裁剪多少，labels列数总比dataset列数少1
    dataSet = datas[1:] #第二行开始就是数据集了
    return dataSet,labels

def readFromDB(dbname="subtreeapi",tablename='',fields=[]):
    db=pymysql.connect("127.0.0.1","root","","subtreeapi",charset="utf8")
    cur = db.cursor()     
    sql = "select "
    for value in fields:
        sql+="`%s`," % (value)
    sql = sql[:-1]
    sql += " from %s " % (tablename)
    #print(sql)
    cur.execute(sql)
    
    #tmpdata = list(cur.fetchall())
    dataSet = []
    #数据库读取返回的是元组，这里通过循环将二维元组化为list
    for line in list(cur.fetchall()):
        dataSet.append(list(line))
    #print(dataSet)
    #这里根据dataset数据列数来决定labels裁剪，总比dataset列数少1
    labels = fields[:len(dataSet[0])-1]
    print("SQL:",sql,"\ndataSet:",dataSet[:10],"\nLabels:",labels)
    return dataSet,labels



#-------------------------II. 树的核心生成算法------------------------------

#2.1 计算信息熵
# 修改了float(...)
def calcShannonEnt(dataSet):
    # 共几行
    numEntries = len(dataSet)
    # 分类类目字典
    labelCounts = {}
    for featVec in dataSet:
        # 取得状态列的值,即判断是正例还是负例
        currentLabel = featVec[-1]
        if currentLabel not in labelCounts.keys():
            labelCounts[currentLabel] = 0.0
        # 字典里有该属性相应计数器就+1，没有就创建一个再+1 ，无论如何都+1
        labelCounts[currentLabel]+= 1.0

    shannonEnt = 0.0
    for key in labelCounts:
        prob = labelCounts[key]/numEntries
        if prob == 0:
            print("!!!!!!!!!!!!")
        shannonEnt -= prob * math.log(prob,2)
    return shannonEnt



# 2.2 按照最大信息增益划分数据集合
# 按照某个特征进行划分的函数,将Prop值为value的数据单独返回
# 参数列表：待划分数据集，特征，分类值
def splitDataSet(dataSet,prop,value):
    retDataSet=[]
    for featVec in dataSet:
        if featVec[prop] == value:
            #这里将参照划分的特征剔除掉了，重新生成一list传回
            reduceFeatVec = featVec[:prop]
            reduceFeatVec.extend(featVec[prop+1:])
            retDataSet.append(reduceFeatVec)
    return retDataSet


# 定义按照最大信息增益划分数据的函数
def chooseBestFeatureToSplit(dataSet):
    # 所有特征数量（方便之后遍历），由于最后的结果状态不算，所以-1
    numFeature = len(dataSet[0])-1
    bestEntropy = calcShannonEnt(dataSet)
    bestInfoGain = 0
    # 最佳特征
    bestFeature = -1

    for i in range(numFeature):
        # 得到某特征的所有值（一列）
        featList = [number[i] for number in dataSet]
        # 使用set()函数得到该特征的所有取值，方便计算信息增益
        uniqualVals = set(featList)
        newEntropy = 0
        for value in uniqualVals:
            # 生成特征名为i，值为value的数据子集
            subDataSet = splitDataSet(dataSet,i,value)
            # 该特征取值的比率
            prob = len(subDataSet)/float(len(dataSet))
            # 各子集熵的和
            newEntropy += prob * calcShannonEnt(subDataSet)
        # 根据信息增益的公式计算出
        infoGain = bestEntropy - newEntropy
        # print("infoGain:",infoGain,"||bestInfoGain:",bestInfoGain)
        if infoGain > bestInfoGain:
            bestInfoGain = infoGain
            bestFeature = i
    return bestFeature

# 2.3 创建决策树构造函数createTree
def majorityCnt(classList):
    # 和求熵时候一样操作，使用一个字典存储结果状态的所有取值
    classCount={}
    for vote in classList:
        if vote not in classCount.keys():
            classCount[vote] = 0
        classCount[vote] += 1
    
    #sortedClassCount = sorted(classCount.items,key=operator.itemgetter(1),revesed=True)
    #return sortedClassCount[0][0]
    # print(classCount)
    return max(classCount)

def createTree(dataSet,labels,text):
    # 选取状态列
    classList = [example[-1] for example in dataSet]
    # 和classList的最后一个元素相同的元素个数与classList长度相等，说明classList中全部是该值，是纯的，应该停止划分
    print("classList:",classList,"  classList[-1]:",classList[-1])
    print("classList.count(classList[-1]):",classList.count(classList[-1])," len(classList):",len(classList))
    if(len(classList)==2):
        print('dataSet:\n',dataSet,'\n----------')
    if classList.count(classList[-1]) == len(classList):
        # 返回的结果是纯的属性值，就是在决策树中的叶子节点：no,yes等
        return  {"name":classList[-1],"col":"null","text":text,"children":"null"}
    # ??
    if len(dataSet[0]) == 1:
        return {"name":majorityCnt(classList),"col":"null","text":text,"children":"null"}
    
    # 按照信息增益最高选取分类特征属性
    #返回分类的特征序号
    bestFeat = chooseBestFeatureToSplit(dataSet)
    # 该特征的label
    bestFeatLabel = labels[bestFeat]
    print("------->",bestFeat,"||",bestFeatLabel)
    if bestFeat == -1:
        return {"name":majorityCnt(classList),"col":"null","text":text,"children":"null"}

    # 构建树字典
    #myTree = {bestFeatLabel:{}}
    myTree = {"name":bestFeatLabel,"col":bestFeat,"text":text,"children":[]}
    # 特征选取一个就删一个
    del(labels[bestFeat])
    # 和上面有一个很类似，用于获得bestFeat的所有取值
    featValues = [example[bestFeat] for example in dataSet]
    uniqualVals = set(featValues)
    for value in uniqualVals:
        # 子集合，此时已删除了最佳特征
        subLabels=labels[:]
        #递归，此时按照最佳子集合不同的值依次生成若干孩子节点，同时labels已经不再有最佳特征，树可以进一步加深
        swap = createTree(splitDataSet(dataSet,bestFeat,value),subLabels,value)
        myTree["children"].append(swap)#createTree(splitDataSet(dataSet,bestFeat,value),subLabels,value))
    return myTree



#-------------------III.分类与属性----------------------
#II.8.1 JsonToDecisionnode辅助函数，根据列名确定列号
def nameToIndex(labels,name):
    for i in range(len(labels)):
        if name == labels[i]:
            return i
    print("name:",name,"return 0")
    return 0

# 3.1 决策树用于分类
# 三个变量，决策树，属性特征，测试数据
def classify(jsonTree,labels,observation):
    #如果是叶子节点
    if jsonTree["children"]=="null":        
        return jsonTree["name"]
    #是分支节点
    else:
        #找到本节点属性列对应的属性值
        v=observation[nameToIndex(labels,jsonTree['name'])]#        
        branch=None
        #如果这个值就是节点的子节点的分支上的引导文字
        for i in range(len(jsonTree["children"])):            
            # print("v:",v,"jsonTree:",jsonTree["children"][i]["text"])
            if v==jsonTree["children"][i]["text"]:                
                branch=jsonTree["children"][i]
        return classify(branch,labels,observation)


#用于获取树深度(内部函数，外部不可调用)
def getTreeDepth(jsonTree):
    #如果不是叶子节点
    if jsonTree["children"] != "null":
        depths = [0]*len(jsonTree["children"])
        for i in range(len(depths)):
            depths[i] = getTreeDepth(jsonTree["children"][i])
        maxDepth = 0
        for i in range(len(depths)):
            if depths[i] > maxDepth:
                maxDepth = depths[i]
        return maxDepth+1
    else:
        return 0


def checkAccuracy(jsonTree,labels,observations): 
    total = float(len(observations))
    if total <= 0:return 0
    correct = 0.0
    for observation in observations:
        # print("data:",observation[:-1])
        result = classify(jsonTree,labels,observation)
        # print("result: 实际值:",observation[-1],"|预测值:",result)
        if str(result) == str(observation[-1]):
            correct += 1.0
    return correct/total


#--------------------------O.总控制函数()----------------------------
#--------------------------------------------------------------------
#根据相关数据生成一棵树
#dataSource:{csv,db}    target:{tree,json,db}
class ID3:
    '''常用变量定义'''
    #数据集合(二维数组)
    dataSet = []
    #数据表头/特征名(一维数组)
    labels = []
    #数据库字段选择器
    fields = []
    #决策树类型(离散型Discrete/连续型Continuous)
    decisionTreeType = ""
    #数据集合
    dataSource="csv"
    #数据源名称
    sourceName=""
    #目标类型{"dictTree,json,biTree,db"}
    target="dictTree"
    #字典树
    dictTree = {}
    #树的相关属性
    depth = 0
    nodes_num = 0
    def __init__(self,dataSource="db",sourceName="",fields=[]):
        #数据集合
        self.dataSource=dataSource
        #数据源名称
        self.sourceName=sourceName
        self.fields = fields
        '''数据源读取'''
        if dataSource == 'csv':
            self.dataSet,self.labels = readFromCSV(sourceName)
            # print('labels:',self.labels,'\n')
            # print('dataSet:',self.dataSet,'\n')
        elif dataSource == "db":
            self.dataSet,self.labels = readFromDB("db_slg",sourceName,self.fields)
            # print('labels:',self.labels,'\n')
            # print('dataSet:',self.dataSet,'\n')
        else:
            # print( "please specify the dataSource, csv or db" )
            return "please specify the dataSource, csv or db" 
        
    def GenerateID3(self,target="dictTree"):   
        '''树训练'''
        self.dictTree = createTree(self.dataSet,self.labels,"text")   
        self.labels = self.fields
        '''树输出'''
        if target == "dictTree":
            # print(self.dictTree)
            return (self.dictTree)
        elif target == "json": 
            # print(json.dumps(self.dictTree))
            return (json.dumps(self.dictTree))
        else:
            # print( "please specify the target, dictTree or json" )
            return "please specify the target, dictTree or json" 

    #外部调用函数，返回树的节点数和深度
    def calcProperties(self):
        #树深度则需要递归得出
        depth = getTreeDepth(self.dictTree) + 1
        #节点数直接通过统计字符串中'name'个数
        jsonTree = json.dumps(self.dictTree)
        nodes_num = jsonTree.count('"name"')
        return nodes_num,depth
    
    # 对新的观测数据进行分类。observation为观测数据。dictTree为训练好的字典树
    def Classify(self,observation):
        return classify(self.dictTree,self.labels,observation)

    
    # 对新的观测数据集进行批量分类。observations为观测数据集。dictTree为训练好的字典树
    def ClassifyAll(self,observations):
        classes = []
        for observation in observations:
            classes.append(classify(self.dictTree,self.labels,observation))
        return classes

    
    #测试精度(dictTree字典树,测试向量集(二维数组))
    def CheckAccuracy(self,dataSource='',sourceName="",fields=[]):   
        '''数据源读取'''
        if dataSource == 'csv':
            dataSet,labels = readFromCSV(sourceName)
            #print('labels:',labels,'\n')
            #print('dataSet:',dataSet,'\n')
        elif dataSource == "db":
            dataSet,labels = readFromDB("db_slg",sourceName,fields)            
        elif dataSource == "list":
            dataSet = sourceName
        else:
            # print( "please specify the dataSource, csv or db" )
            return "please specify the dataSource, csv or db" 
        
        # print('CheckAccuracy DataSet:',dataSet,'\n')
        return checkAccuracy(self.dictTree,self.labels,dataSet)


#------------------模块直接执行-----------------------
if __name__=='__main__':  #只有在执行当前模块时才会运行此函数
    #target为dictTree，返回字典树
    ID3_controller = ID3("db","playtennis_one_4",['outlook','temperature','humidity','windy','result'])#四级,六级,政治面貌,计算机等级,综合能力,性别,去向
    #ID3_controller = ID3("db","forecast2",['四级','六级','政治面貌','计算机等级','综合能力','性别','result'])
    ID3_controller.GenerateID3("json")
    #使用这颗字典树进行分类预测
    #print(ID3_controller.Classify(['Sunny','Hot','High','Weak']))
    #print(ID3_controller.ClassifyAll([['sunny','hot','high','false'],['overcast','cool','normal','true']]))
    #使用数据库数据进行精度预测
    print(ID3_controller.CheckAccuracy("db","playtennis_one_4",['outlook','temperature','humidity','windy','result']))
    #print(ID3_controller.CheckAccuracy("db","forecast2",['四级','六级','政治面貌','计算机等级','综合能力','性别','result']))
    #也可以直接传list值[['sunny','hot','high','false'],['overcast','cool','normal','true']]))
    #print(ID3_controller.CheckAccuracy("list",[['sunny','hot','high','false','N'],['overcast','cool','normal','true','Y']]))
    #树的节点树，深度等
    print(ID3_controller.calcProperties())







