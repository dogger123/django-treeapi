import operator
import re
import json
import pymysql
#------------------------I.数据读取----------------------------
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

def readFromDB(tablename='',fields=[]):
    db=pymysql.connect("127.0.0.1","root","","subtreeapi",charset="utf8")
    cur = db.cursor()
    sql = "select "
    for value in fields:
        sql+="`%s`," % (value)
    sql = sql[:-1]
    sql += "from %s where `%s` != '-' " % (tablename,fields[-1])
    cur.execute(sql)
    
    #tmpdata = list(cur.fetchall())
    dataSet = []
    #数据库读取返回的是元组，这里通过循环将二维元组化为list
    for line in list(cur.fetchall()):
        dataSet.append(list(line))
    for i  in range(len(dataSet)):
        #最后一列不需要数据清洗，一定有值，只是需要离散话映射
        for j in range(len(dataSet[i])-1):
            if dataSet[i][j] == '-':
                dataSet[i][j] = 0.0
            dataSet[i][j] = float(dataSet[i][j])
        dataSet[i][-1] = resultDiscretization(dataSet[i][-1])
    #这里根据dataset数据列数来决定labels裁剪，总比dataset列数少1

    labels = fields[:len(dataSet[0])-1]
    print(sql,"\n",dataSet[:10],"\n",labels)
    return dataSet,labels

def resultDiscretization(origin):
    origin = float(origin)
    #上无上限，下无下限
    if origin >= 90:
      return "excellent"
    elif origin >= 80 and origin <= 89:
      return "good"
    elif origin >= 60 and origin <= 79:
      return "pass"
    else:
      return "failed"
#------------------------IT.算法核心----------------------------
def calGini(dataSet):
    numEntries = len(dataSet)
    labelCounts={}
    for featVec in dataSet: 
        currentLabel = featVec[-1]
        if currentLabel not in labelCounts.keys(): labelCounts[currentLabel] = 0
        labelCounts[currentLabel] += 1
    gini=1
    for label in labelCounts.keys():
        prop=float(labelCounts[label])/numEntries
        gini -=prop*prop
    return gini


def splitDataSet(dataSet, axis, value,threshold):
    retDataSet = []
    if threshold == 'lt':
        for featVec in dataSet:
            if featVec[axis] <= value:
                retDataSet.append(featVec)
    else:
        for featVec in dataSet:
            if featVec[axis] > value:
                retDataSet.append(featVec)

    return retDataSet

def majorityCnt(classList):
    classCount={}
    for vote in classList:
        if vote not in classCount.keys(): classCount[vote] = 0
        classCount[vote] += 1
    sortedClassCount = sorted(classCount.iteritems(), key=operator.itemgetter(1), reverse=True)
    return sortedClassCount[0][0]


def chooseBestFeatureToSplit(dataSet):
    numFeatures = len(dataSet[0]) - 1
    bestGiniGain = 1.0; bestFeature = -1;bsetValue=""
    for i in range(numFeatures):        #遍历特征
        featList = [example[i] for example in dataSet]#得到特征列
        uniqueVals = list(set(featList))       #从特征列获取该特征的特征值的set集合
        uniqueVals.sort()
        for value in uniqueVals:# 遍历所有的特征值
            GiniGain = 0.0
            # 左增益
            left_subDataSet = splitDataSet(dataSet, i, value,'lt')
            left_prob = len(left_subDataSet)/float(len(dataSet))
            GiniGain += left_prob * calGini(left_subDataSet)
            # print left_prob,calGini(left_subDataSet),
            # 右增益
            right_subDataSet = splitDataSet(dataSet, i, value,'gt')
            right_prob = len(right_subDataSet)/float(len(dataSet))
            GiniGain += right_prob * calGini(right_subDataSet)
            # print right_prob,calGini(right_subDataSet),
            # print GiniGain
            if (GiniGain < bestGiniGain):       #比较是否是最好的结果
                bestGiniGain = GiniGain         #记录最好的结果和最好的特征
                bestFeature = i
                bsetValue=value
    return bestFeature,bsetValue

def createTree(dataSet,labels,text):
    classList = [example[-1] for example in dataSet]
    # print dataSet
    if classList.count(classList[0]) == len(classList):
        return {"name":classList[0],"col":"null","text":text,"children":"null"}#所有的类别都一样，就不用再划分了
    if len(dataSet) == 1: #如果没有继续可以划分的特征，就多数表决决定分支的类别
        return {"name":majorityCnt(classList),"col":"null","text":text,"children":"null"}
    bestFeat,bsetValue = chooseBestFeatureToSplit(dataSet)
    # print bestFeat,bsetValue,labels
    bestFeatLabel = labels[bestFeat]
    if bestFeat==-1:
        return majorityCnt(classList)
    myTree = {"name":bestFeatLabel,"col":bestFeat,"text":text,"children":[{},{}]}
    featValues = [example[bestFeat] for example in dataSet]
    uniqueVals = list(set(featValues))
    subLabels = labels[:]
    # print bsetValue
    #myTree[bestFeatLabel][bestFeatLabel+'<='+str(round(float(bsetValue),3))] = createTree(splitDataSet(dataSet, bestFeat, bsetValue,'lt'),subLabels)
    myTree["children"][0] = createTree(splitDataSet(dataSet,bestFeat,bsetValue,'lt'),subLabels,'<='+str(round(float(bsetValue),3)))
    #myTree[bestFeatLabel][bestFeatLabel+'>'+str(round(float(bsetValue),3))] = createTree(splitDataSet(dataSet, bestFeat, bsetValue,'gt'),subLabels)
    myTree["children"][1] = createTree(splitDataSet(dataSet, bestFeat, bsetValue,'gt'),subLabels,'>'+str(round(float(bsetValue),3)))
    return myTree

#----------------------III.分类评价--------------------------
#连续型分类不同于离散型
def classify(jsonTree,observation):
    #如果是叶子节点
    if jsonTree["children"]=="null":
        return jsonTree["name"]
    #是分支节点
    else:
        #找到本节点属性列对应的属性值
        v=float(observation[jsonTree['col']])#nameToIndex(jsonTree['name'],labels)]
        branch=None
        #如果这个值符合节点的子节点的分支上的引导文字中指定的数字范围
        threshold = re.findall(r"\d+\.?\d*",jsonTree["children"][0]["text"])[0]
        if v > float(threshold):
            branch=jsonTree["children"][0]
        else:
            branch=jsonTree["children"][1]
        return classify(branch,observation)


def checkAccuracy(jsonTree,observations):    
    total = float(len(observations))
    if total <= 0:return 0
    correct = 0.0
    for observation in observations:
        print("data:",observation[:-1])
        result = classify(jsonTree,observation)
        print("result: T:",observation[-1],"|P:",result)
        if str(result) == str(observation[-1]):
            correct += 1.0
    return correct/total


#--------------------------O.总控制函数()----------------------------
#--------------------------------------------------------------------
#根据相关数据生成一棵树
#dataSource:{csv,db}    target:{tree,json,db}
def GenerateCART(dataSource="csv",sourceName="",target="dictTree",fields=[]):
    '''常用变量定义'''
    #数据集合(二维数组)
    dataSet = []
    #数据表头/特征名(一维数组)
    labels = []
    #字典树
    dictTree = {}
 
    '''数据源读取'''
    if dataSource == 'csv':
        dataSet,labels = readFromCSV(sourceName)
        print('labels:',labels,'\n')
        print('dataSet:',dataSet,'\n')
    elif dataSource == "db":
        dataSet,labels = readFromDB(sourceName,fields)
        print('labels:',labels,'\n')
        print('dataSet:',dataSet,'\n')
    else:
        print( "please specify the dataSource, csv or db" )
        return "please specify the dataSource, csv or db" 

    '''树训练'''
    dictTree = createTree(dataSet,labels,"null")

    '''树输出'''
    if target == "dictTree":
        print(dictTree)
        return dictTree
    elif target == "db":
        pass
    elif target == "json":
        print(json.dumps(dictTree))
        return (json.dumps(dictTree))
    else:
        print( "please specify the target, csv or db" )
        return "please specify the target, csv or db" 

# 对新的观测数据进行分类。observation为观测数据。dictTree为训练好的字典树
def Classify(dictTree,observation):
    return classify(dictTree,observation)

# 对新的观测数据集进行批量分类。observations为观测数据集。dictTree为训练好的字典树
def ClassifyAll(dictTree,observations):
    classes = []
    for observation in observations:
        classes.append(classify(dictTree,observation))
    return classes

# 计算精确度
def CheckAccuracy(jsonTree,dataSource,sourceName):
    '''数据源读取'''
    if dataSource == 'csv':
        dataSet,labels = readFromCSV(sourceName)
        #print('labels:',labels,'\n')
        #print('dataSet:',dataSet,'\n')
    elif dataSource == "db":
        #print('labels:',labels,'\n')
        print('dataSet:',dataSet,'\n')
    else:
        print( "please specify the dataSource, csv or db" )
        return "please specify the dataSource, csv or db" 
    return checkAccuracy(jsonTree,dataSet)


#----------------------模块直接执行--------------------------
if __name__ == '__main__':
    #dictTree = GenerateCART("csv","datasets/iris_train","dictTree")
    dictTreeJson = GenerateCART("db","personal_transcripts_cs","json",['English','CET4','CET6','AdvancedMath','LinearAlgebra','ProbabilityTheory','DataStructure','DataBase','ComputerNetwork','OperatingSystem','CompositionPrinciple','CppProgramming','ProgrammingPractice','JavaProgramming','CSorSE','NCRE_CPP2'])
    print(dictTreeJson)
    #dataSet,labels = 
    #readFromDB('personal_transcripts_cs',['English','CET4','CET6','AdvancedMath','LinearAlgebra','ProbabilityTheory','DataStructure','DataBase','ComputerNetwork','OperatingSystem','CompositionPrinciple','CppProgramming','ProgrammingPractice','JavaProgramming','CSorSE','NCRE_CPP2'])
    #print('ACC:{:.2%}'.format(checkAccuracy(dictTree,dataSet)))
    #readFromDB('personal_transcripts_cs',['English','CET4','CET6','AdvancedMath','LinearAlgebra','ProbabilityTheory','DataStructure','DataBase','ComputerNetwork','OperatingSystem','CompositionPrinciple','CppProgramming','ProgrammingPractice','JavaProgramming','CSorSE','NCRE_CPP2'])

#----------------------其他参考函数--------------------------
def createTree_old(dataSet,labels):
    classList = [example[-1] for example in dataSet]
    # print dataSet
    if classList.count(classList[0]) == len(classList):
        return classList[0]#所有的类别都一样，就不用再划分了
    if len(dataSet) == 1: #如果没有继续可以划分的特征，就多数表决决定分支的类别
        return majorityCnt(classList)
    bestFeat,bsetValue = chooseBestFeatureToSplit(dataSet)
    # print bestFeat,bsetValue,labels
    bestFeatLabel = labels[bestFeat]
    if bestFeat==-1:
        return majorityCnt(classList)
    myTree = {bestFeatLabel:{}}
    featValues = [example[bestFeat] for example in dataSet]
    uniqueVals = list(set(featValues))
    subLabels = labels[:]
    # print bsetValue
    myTree[bestFeatLabel][bestFeatLabel+'<='+str(round(float(bsetValue),3))] = createTree(splitDataSet(dataSet, bestFeat, bsetValue,'lt'),subLabels)
    myTree[bestFeatLabel][bestFeatLabel+'>'+str(round(float(bsetValue),3))] = createTree(splitDataSet(dataSet, bestFeat, bsetValue,'gt'),subLabels)
    return myTree
