import pymysql
import json

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
                dataSet[i][j] = 'failed'
    #这里根据dataset数据列数来决定labels裁剪，总比dataset列数少1
    labels = fields[:len(dataSet[0])-1]
    print(sql,"\n",dataSet[:10],"\n",labels)
    return dataSet,labels


# I.2 测试用数据集合
def createDataSet():
    labels=["company","country","experience","age"]
    dataSet=[
         ['slashdot','USA','yes',18,'None'],
         ['google','France','yes',23,'Premium'],
         ['digg','USA','yes',24,'Basic'],
         ['kiwitobes','France','yes',23,'Basic'],
         ['google','UK','no',21,'Premium'],
         ['(direct)','New Zealand','no',12,'None'],
         ['(direct)','UK','no',21,'Basic'],
         ['google','USA','no',24,'Premium'],
         ['slashdot','France','yes',19,'None'],
         ['digg','USA','no',18,'None'],
         ['google','UK','no',18,'None'],
         ['kiwitobes','UK','no',19,'None'],
         ['digg','New Zealand','yes',12,'Basic'],
         ['slashdot','UK','no',21,'None'],
         ['google','UK','yes',18,'Basic'],
         ['kiwitobes','France','yes',19,'Basic']]
    ''' 
    labels=["overcase","temp","humidity","windy"]
    dataSet = [
         ["sunny","hot","high","false","N"],
         ["sunny","hot","high","true","N"],
         ["overcast","hot","high","false","Y"],
         ["rain","mild","high","false","Y"],
         ["rain","cool","normal","false","Y"],
         ["rain","cool","normal","true","N"],
         ["overcast","cool","normal","true","Y"],
    ]
    '''
    return dataSet,labels

#-----------------II. 决策树生成核心算法------------------------
#II.1 决策树的节点类
class decisionnode:
    def __init__(self,col=-1,colName="",value=None,results=None,tb=None,fb=None):
        self.col=col                #待检测条件所属的列索引。即当前是对第几列数据进行分类
        self.colName=colName
        self.value=value            #为使结果为true，当前列必须匹配的值
        self.results=results        #如果当前节点时叶节点，表示该节点的结果值，如果不是叶节点，为None
        self.tb=tb                  #判断条件为true后的子节点
        self.fb=fb                  #判断调节为false后的子节点

#II.2 拆分数据集合
# 根据某一属性对数据集合进行拆分，能够处理数值型数据或名词性数据。其实决策树只能处理离散型数据，对于连续性数据也是划分为范围区间块
# rows样本数据集，column要匹配的属性列索引，value指定列上的数据要匹配的值
def divideset(rows,column_index,column_value):
    # 定义一个函数，令其告诉我们数据行属于第一组（返回值为true）还是第二组（返回值false）
    split_function=None
    if isinstance(column_value,int) or isinstance(column_value,float):
        split_function=lambda row:row[column_index]>=column_value   #按大于、小于区分
    else:
        split_function=lambda row:row[column_index]==column_value   #按等于、不等于区分

    # 将数据集拆分成两个子集，并返回
    set1=[row for row in rows if split_function(row)]
    set2=[row for row in rows if not split_function(row)]
    return (set1,set2)

#II.3 计算基尼不纯度
#rows样本数据集
def giniimpurity(rows):
    total=len(rows)
    counts=uniquecounts(rows)
    imp=0
    for k1 in counts:
        p1=float(counts[k1])/total
        for k2 in counts:
            if k1==k2: continue
            p2=float(counts[k2])/total
            imp+=p1*p2
    return imp

#rows样本数据集
def entropy(rows):
    from math import log
    log2=lambda x:log(x)/log(2)
    results=uniquecounts(rows)
    # 此处开始计算熵的值
    ent=0.0
    for r in results.keys():
        p=float(results[r])/len(rows)
        ent=ent-p*log2(p)
    return ent

#II.4 统计某行中的所有取值
# 统计集合rows中每种分类的样本数目。（样本数据每一行数据的最后一列记录了分类结果）。rows样本数据
def uniquecounts(rows,index="null"):
    results={}
    for row in rows:
        # 目标结果在样本数据最后一列
        #r=row[len(row)-1]
        if index=="null":
            i = len(row)-1
        else:
            i = index
        r = row[i]
        if r not in results:
            results[r]=0
        results[r]+=1
    return results


#II.5 构建决策树，递归函数
# 构建决策树.scoref为信息增益的计算函数
def buildtree(rows,labels,scoref=giniimpurity):
    if len(rows)==0: return decisionnode()
    current_score=scoref(rows)

    # 定义一些变量以记录最佳拆分条件
    best_gain=0.0
    best_criteria=None
    best_sets=None

    column_count=len(rows[0])-1
    for col in range(0,column_count):    #遍历每一列（除最后一列，因为最后一列是目标结果）
        # 在当前列中生成一个由不同值构成的序列
        column_values={}
        for row in rows:
            column_values[row[col]]=1
        # 接下来根据这一列中的每个值，尝试对数据集进行拆分
        for value in column_values.keys():
            (set1,set2)=divideset(rows,col,value)

            # 计算信息增益
            p=float(len(set1))/len(rows)
            gain=current_score-p*scoref(set1)-(1-p)*scoref(set2)
            if gain>best_gain and len(set1)>0 and len(set2)>0:   #找到信息增益最大的分类属性
                best_gain=gain
                best_criteria=(col,value)
                best_sets=(set1,set2)
    # 创建子分支
    if best_gain>0:
        trueBranch=buildtree(best_sets[0],labels)   #创建分支
        falseBranch=buildtree(best_sets[1],labels)  #创建分支
        return decisionnode(col=best_criteria[0],colName=labels[best_criteria[0]],value=best_criteria[1],tb=trueBranch,fb=falseBranch)  #返回决策树节点
    else:
        return decisionnode(results=uniquecounts(rows))


#II.6 生成Json/字典树(特征取值写在节点上)
def generateJson_Old(tree,labels,text):
    #是分支节点，name是属性名，传给后代的两个text是value 和 not vavlue
    if tree.results==None:
        myTree={"name":str(labels[tree.col]),"text":text,"children":[{},{}]}
        myTree["children"][0]=generateJson(tree.tb,labels,str(tree.value))
        myTree["children"][1]=generateJson(tree.fb,labels,"not " + str(tree.value))
    #是叶子节点，name 是分类结果
        return myTree
    else:
        txt=""
        for key in tree.results.keys():
            txt+=str(key)
            txt+=' '
        return {"name":txt,"text":text,"children":"null"}

#II.7 生成Json/字典树(特征取值写在分支上)
def generateJson(dataSet,tree,labels,text):
    #是分支节点，name是属性名，传给后代的两个text是value 和 not vavlue
    if tree.results==None:
        myTree={"name":str(labels[tree.col]),"col":tree.col,"text":text,"children":[{},{}]}
        myTree["children"][0]=generateJson(dataSet,tree.tb,labels,str(tree.value))
        #不是这个取值，应该是tree.col列的其他取值
        allVals = uniquecounts(dataSet,tree.col)
        allVals.pop(str(tree.value))
        otherVals=""
        for value in allVals: 
            otherVals += str(value)
            otherVals += " or "
        #去除多余的" or "
        otherVals = otherVals[:-4]
        #print("---> tree.vlue:",tree.value,str(tree.value),"|",str(otherVals),"|",uniquecounts(dataSet,tree.col),"|",allVals)
        myTree["children"][1]=generateJson(dataSet,tree.fb,labels,otherVals)
    #是叶子节点，name 是分类结果
        return myTree
    else:
        txt=""
        for key in tree.results.keys():
            txt+=str(key)
        return {"name":txt,"col":"null","text":text,"children":"null"}

#II.8.1 JsonToDecisionnode辅助函数，根据列名确定列号
def nameToIndex(labels,name):
    for i in range(len(labels)):
        if name == labels[i]:
            return i
    return 0

#II.8.2 从字典树构建一个二叉树
def JsonToDecisionnode(jsonTree,root,labels):
    if root == None:
        root = decisionnode()
    #如果为叶子节点
    if jsonTree["children"] == "null":
        #root.col = nameToIndex(json["name"])
        dictResults = {}
        results = list(jsonTree["name"].split(" or "))#.rstrip().split(" or "))
        for value in results:
            dictResults[value]=1
        print("dictResults:\n",dictResults)
        root.results = dictResults
    #如果是分支节点
    else:
        #root.col = nameToIndex(labels,jsonTree["name"])
        root.col = jsonTree["col"]
        root.colName = jsonTree["name"]
        #分支节点的value，看其true分支的text是什么即可
        root.value = jsonTree["children"][0]["text"]
        root.tb = JsonToDecisionnode(jsonTree["children"][0],root.tb,labels)
        root.fb = JsonToDecisionnode(jsonTree["children"][1],root.fb,labels)
    return root

#--------------------------III.分类和评定---------------------------------
def classify_Old(tree,observation):
    if tree.results!=None:
        return tree.results
    else:
        v=observation[tree.col]
        branch=None
        if isinstance(v,int) or isinstance(v,float):
            if v>=tree.value: branch=tree.tb
            else: branch=tree.fb
        else:
            if v==tree.value: branch=tree.tb
            else: branch=tree.fb
        return Classify(branch,observation)

def classify(jsonTree,observation):
    #如果是叶子节点
    if jsonTree["children"]=="null":
        return jsonTree["name"]
    #是分支节点
    else:
        #找到本节点属性列对应的属性值
        v=observation[jsonTree['col']]#nameToIndex(jsonTree['name'],labels)]
        branch=None
        #如果这个值就是节点的子节点的分支上的引导文字
        if v==jsonTree["children"][0]["text"]:
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

# 决策树剪枝。(因为有些属性的分类产生的熵值的差太小，没有区分的必要)，mingain为门限。
# 为了避免遇到大小台阶的问题（子树分支的属性比较重要），所以采取先建树，再剪支的方式
def prune(tree,mingain):
    # 如果分支不是叶节点，则对其进行剪枝操作
    if tree.tb.results==None:
        prune(tree.tb,mingain)
    if tree.fb.results==None:
        prune(tree.fb,mingain)

    # 如果两个自分支都是叶节点，则判断他们是否需要合并
    if tree.tb.results!=None and tree.fb.results!=None:
        # 构建合并后的数据集
        tb,fb=[],[]
        for v,c in tree.tb.results.items():
            tb+=[[v]]*c
        for v,c in tree.fb.results.items():
            fb+=[[v]]*c

        # 检查熵的减少情况
        delta=entropy(tb+fb)-(entropy(tb)+entropy(fb)/2)
        print(delta)
        if delta<mingain:
            # 合并分支
            tree.tb,tree.fb=None,None
            tree.results=uniquecounts(tb+fb)
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
    #cart树
    cartTree = decisionnode()
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
    cartTree = buildtree(dataSet,labels)
    prune(cartTree,0.8)
    '''树输出'''
    if target == "dictTree":
        dictTree = generateJson(dataSet,cartTree,labels,"null")
        #print(dictTree)
        return (dictTree)
    elif target == "db":
        pass
    elif target == "biTree":
        return cartTree
    elif target == "json":
        dictTree = generateJson(dataSet,cartTree,labels,"null")
        #print(json.dumps(dictTree))
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



#------------------模块直接执行-----------------------
if __name__=='__main__':  #只有在执行当前模块时才会运行此函数
    #dictTree = GenerateCART("csv","datasets/JSNCRE_vcpp_train","dictTree")
    dictTree = GenerateCART("db","personal_transcripts_discrete_cs","dictTree",['English','CET4','CET6','AdvancedMath','LinearAlgebra','ProbabilityTheory','DataStructure','DataBase','ComputerNetwork','OperatingSystem','CompositionPrinciple','CppProgramming','ProgrammingPractice','JavaProgramming','CSorSE','NCRE_CPP2'])
    #print(classify(dictTree,['sunny','hot','high','false']))
    print(json.dumps(dictTree))
    #dataSet,labels = readFromCSV("datasets/JSNCRE_vcpp_test")
    #print('accuracy: {:.2%}'.format(checkAccuracy(dictTree,dataSet)))
