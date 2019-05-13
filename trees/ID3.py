import math
from math import log
import operator

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


# 1.构造数据集函数createDataSet()
def createDataSet():
    # 训练数据集
    dataSet = [[1, 1, 'yes'], [1, 1, 'yes'], [1, 0, 'no'], [0, 1, 'no'], [0, 1, 'no']]
    # 所有属性
    labels = ['no surfacing', 'flippers']
    return dataSet, labels


# def readFromCSV(filename='data.csv'):
#     with open(filename) as f:
#         reader = csv.DictReader(f)
#         # 将使用一个list存储reader中每一行(orderedDict类型)
#         datas = []
#         for row in reader:
#             datas.append(row)
#     return datas


# 从csv文件族中获取数据集和标签
# 标签集应以xxxx_labels.csv为名字
# 数据集应以xxxx_datas.csv为名字
# 直接指定xxxx即可自动读取两个文件得到dataSet和labels两个数组
def readFromCSVs(filename='data'):
    # 数据集相关变量
    f = open(filename + "_datas.csv")
    dataSet = []
    # 开始读取数据集
    line = f.readline()
    for line in f:
        # print(line)
        newline = line.strip('\n').split(',')
        print(newline)
        # 最后返回dataSet
        dataSet.append(newline)
    f.close()

    # 标签集相关变量
    f = open(filename + "_labels.csv")
    labels = f.readline().strip('\n').split(',')
    return dataSet, labels


# 2.1 计算信息熵
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
        labelCounts[currentLabel] += 1.0

    shannonEnt = 0.0
    for key in labelCounts:
        prob = labelCounts[key] / numEntries
        if prob == 0:
            print("!!!!!!!!!!!!")
        shannonEnt -= prob * math.log(prob, 2)
    return shannonEnt


# 2.2 按照最大信息增益划分数据集合
# 按照某个特征进行划分的函数,将Prop值为value的数据单独返回
# 参数列表：待划分数据集，特征，分类值
def splitDataSet(dataSet, prop, value):
    retDataSet = []
    for featVec in dataSet:
        if featVec[prop] == value:
            # 这里将参照划分的特征剔除掉了，重新生成一list传回
            reduceFeatVec = featVec[:prop]
            reduceFeatVec.extend(featVec[prop + 1:])
            retDataSet.append(reduceFeatVec)
    return retDataSet


# 定义按照最大信息增益划分数据的函数
def chooseBestFeatureToSplit(dataSet):
    # 所有特征数量（方便之后遍历），由于最后的结果状态不算，所以-1
    numFeature = len(dataSet[0]) - 1
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
            subDataSet = splitDataSet(dataSet, i, value)
            # 该特征取值的比率
            prob = len(subDataSet) / float(len(dataSet))
            # 各子集熵的和
            newEntropy += prob * calcShannonEnt(subDataSet)
        # 根据信息增益的公式计算出
        infoGain = bestEntropy - newEntropy

        if infoGain > bestInfoGain:
            bestInfoGain = infoGain
            bestFeature = i
    return bestFeature


# 2.3 创建决策树构造函数createTree
def majorityCnt(classList):
    # 和求熵时候一样操作，使用一个字典存储结果状态的所有取值
    classCount = {}
    for vote in classList:
        if vote not in classCount.keys():
            classCount[vote] = 0
        classCount[vote] += 1
    sortedClassCount = sorted(classCount.items, key=operator.itemgetter(1), revesed=True)
    return sortedClassCount[0][0]


def createTree(dataSet, labels,text):
    # 选取状态列
    classList = [example[-1] for example in dataSet]
    # 和classList的最后一个元素相同的元素个数与classList长度相等，说明classList中全部是该值，是纯的，应该停止划分
    if classList.count(classList[-1]) == len(classList):
        # 返回的结果是纯的属性值，就是在决策树中的叶子节点：no,yes等
        #return classList[-1]
        return {"name": classList[0], "text": text, "children": "null"}
    # ??
    if len(classList[0]) == 1:
        #return majorityCnt(classList)
        return {"name": majorityCnt(classList), "text": text,"children":"null"}

    # 按照信息增益最高选取分类特征属性
    # 返回分类的特征序号
    bestFeat = chooseBestFeatureToSplit(dataSet)
    # 该特征的label
    bestFeatLabel = labels[bestFeat]

    # 构建树字典
    #myTree = {bestFeatLabel: {}}
    myTree = {"name": bestFeatLabel, "text": text, "children": []}
    # 特征选取一个就删一个
    del (labels[bestFeat])
    # 和上面有一个很类似，用于获得bestFeat的所有取值
    featValues = [example[bestFeat] for example in dataSet]
    uniqualVals = set(featValues)
    for value in uniqualVals:
        # 子集合，此时已删除了最佳特征
        subLabels = labels[:]
        # 递归，此时按照最佳子集合不同的值依次生成若干孩子节点，同时labels已经不再有最佳特征，树可以进一步加深
        #myTree[bestFeatLabel][value] = createTree(splitDataSet(dataSet, bestFeat, value), subLabels)
        myTree['children'].append(createTree(splitDataSet(dataSet, bestFeat, value), subLabels, value))
    return myTree
#{"root":{"left":"Y","right":"N"}}
#{"name":"root","text":"null","children":[{"name":"Y,"text":"left","children":"null"},"name":"N,"text":"right","children":"null"},]}

# 3.1 决策树用于分类
# 三个变量，决策树，属性特征，测试数据
def classify(inputTree, featLabels, testVec):
    # 树的第一个属性名
    firstStr = list(inputTree.keys())[0]
    # 树的分支，子集合Dict
    secondDict = inputTree[firstStr]
    # 获取决策树第一层在featLabels中的位置
    featIndex = featLabels.index(firstStr)
    for key in secondDict.keys():
        # 用于找到树的第一个属性名（根）
        if testVec[featIndex] == key:
            # 它递归的条件是它下面是另一个树，而不是string类型，因为如果这样就表示该树已经到叶子节点
            if type(secondDict[key]).__name__ == 'dict':
                classLabel = classify(secondDict[key], featLabels, testVec)
            # 如果下面不是树，那一定就是叶子节点，即得到了分类的类型，任务结束
            else:
                classLabel = secondDict[key]
    return classLabel


# 3.2 存储与读取
# 存储函,使用pickle序列化
def storeTree(inputTree, filename):
    import pickle
    # 默认二进制打开
    fw = open(filename, 'wb')
    pickle.dump(inputTree, fw)
    fw.close()


def grabTree(filename):
    import pickle
    fr = open(filename, 'rb')
    return pickle.load(fr)



trainDataSet,labels = readFromCSVs('../upload/forecast2')
myTree = createTree(trainDataSet,labels,"null")
print(myTree)

'''
序号	不浮出水面是否可以生存	是否有脚蹼	是否属于鱼类
1	是                  	是      	是
2	是                 	是      	是
3	是              	否      	否
4	否              	是      	否
5	否              	是      	否
'''

'''
使用说明：
1. 训练决策树：
引入模块
import isFish
通过内部函数创建数据集合
myDat,labels = trees.createDataSet()
查看数据集合
myDat
查看分类标签
labels
创建决策树
myTree=isFish.createTree(myDat,labels)
查看决策树
MyTree


2. 使用训练好的树进行预测：
trees.classify(myTree,labels,[1,0])
trees.classify(myTree,labels,[1,1])

3. 存储决策树
存储
isFish.storeTree(myTree,'store.txt')
读取
isFish.grabTree(myTree,'store.txt')

4. 绘制树
isFish.createPlot(myTree)
'''
