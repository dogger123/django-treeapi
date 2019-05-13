'''
标准CART算法脚本

输入：
    1. 从1个第0行为特征名，其余行为数据的csv文件读入
    2. 从数据库读入
输出:
    1. 生成一个json字符串
    2. 可以打开浏览器展示图片
    3. 可以生成一条sql插入树信息到指定数据库
特性:
    1. 自动判断数据集为连续型或是离散型(连续型/离散型不允许有任何一列是离散型/连续型的)
    2. 通过调用两个CART算法模块实现上述功能
'''


#------------------------I.数据读取----------------------------
from trees.utils.Standard_CART import CART_Discrete
from trees.utils.Standard_CART import CART_Continuous
import pymysql
# I.1 从一个有表头的csv文件读取数据判断是否为离散型
def identifyType_csv(filename='data'):
    f = open(filename+".csv")
    line = f.readline()
    line = f.readline()
    newline = line.strip('\n').split(',')
    #连续型的最后一列可能是字符串，应该去除
    line = newline[:-1]
    for value in line:
        print(value,"\nis?",is_number(value))
        if is_number(value):
            pass
        else:
            return "Discrete"
    return "Continuous"

def identifyType_db(tablename='',fields=[]):
    db=pymysql.connect("127.0.0.1","root","","subtreeapi",charset="utf8")
    cur = db.cursor()
    sql = "select "
    for value in fields:
        sql+="`%s`," % (value)
    sql = sql[:-1]
    sql += "from %s where `%s` != '-' limit 1" % (tablename,fields[-1])
    cur.execute(sql)
    #数据库读取返回的是元组，这里转化为list注意最有一列结果列不需要测试
    tmpdata = list(cur.fetchall()[0][:-1])
    print(sql,"\n",tmpdata)

    for value in tmpdata:
        print(type(value),"\nis?",is_number(value))
        if value == '-' or is_number(value):
            pass
        else:
            return "Discrete"
    return "Continuous"

#----------------------工具函数--------------------------
def is_number(s):
    try:
        complex(s) # for int, long, float and complex
    except ValueError:
        return False
    return True

#----------------------总控函数--------------------------
class CART:
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

    def __init__(self,dataSource="csv",sourceName="",fields=[]):
        #数据集合
        self.dataSource=dataSource
        #数据源名称
        self.sourceName=sourceName
        self.fields = fields
        '''读取数据判断类型'''
        if dataSource == 'csv':
            self.decisionTreeType = identifyType_csv(sourceName)
        elif dataSource == "db":
            print("in db mode")
            self.decisionTreeType = identifyType_db(sourceName,fields)
        else:
            print( "please specify the dataSource, csv or db")

    def GenerateCART(self,target="dictTree"):
        '''调用模块'''
        if self.decisionTreeType == "Discrete":
            #生成离散特有中间树：cartTree
            self.dictTree = CART_Discrete.GenerateCART(self.dataSource,self.sourceName,target,self.fields)
            print(self.dictTree)
        elif self.decisionTreeType == "Continuous":
            self.dictTree = CART_Continuous.GenerateCART(self.dataSource,self.sourceName,target,self.fields)
            print(self.dictTree)
        else:
            print('GenerateCART Error!')
        return self.dictTree 

    def Classify(self,observation):
        if self.decisionTreeType == "Discrete":
            resultDict = CART_Discrete.Classify(self.dictTree,observation)
        elif self.decisionTreeType == "Continuous":
            resultDict = CART_Continuous.Classify(self.dictTree,observation) 
        else:
            print('Classify Error!')
            resultDict = {}
        print(observation , " => ",resultDict)
        return resultDict

    def ClassifyAll(self,observations):
        if self.decisionTreeType == "Discrete":
            resultDict = CART_Discrete.ClassifyAll(self.dictTree,observations) 
        elif self.decisionTreeType == "Continuous":
            resultDict = CART_Continuous.ClassifyAll(self.dictTree,observations) 
        else:
            print('ClassifyAll Error!')
            resultDict = {}
        print(observations , " => ",resultDict)
        return resultDict
    
    def CheckAccuracy(self,dataSource='csv',sourceName=""):
        if self.decisionTreeType == "Discrete":
            accuracy = CART_Discrete.CheckAccuracy(self.dictTree,dataSource,sourceName)
        elif self.decisionTreeType == "Continuous":
            accuracy = CART_Continuous.CheckAccuracy(self.dictTree,dataSource,sourceName)
        else:
            print('CheckAccuracy Error!')
            accuracy = 0.0
        print ('accuracy:{:.2%}'.format(accuracy))
        return accuracy

    def DrawTree(self):
        import os,json
        cmd = "firefox 'http://api.crepuscule.xyz/weixinapi/drawtree?json="
        cmd += json.dumps(self.dictTree)
        cmd += "'"
        #print(cmd)
        os.system(cmd)
        
#----------------------模块直接执行--------------------------
if __name__ == '__main__':
    #control = CART('csv','datasets/JSNCRE_vcpp')
    #control = CART('csv','datasets/NCRE_cpp2_one')
    #control = CART('csv','datasets/COM_vcpp_c')
    #control = CART('csv','datasets/iris')
    #control = CART('db','personal_transcripts_cs',fields=['English','CET4','CET6','AdvancedMath','LinearAlgebra','ProbabilityTheory','DataStructure','DataBase','ComputerNetwork','OperatingSystem','CompositionPrinciple','CppProgramming','ProgrammingPractice','JavaProgramming','CSorSE','NCRE_CPP2'])#,'NCRE_NET3'])
    #control.GenerateCART()
    '''
    control.ClassifyAll(
            [['presbyopic','myope','yes','normal'],
             ['presbyopic','hyper','no','reduced'],  
             ['presbyopic','hyper','no','normal'],  
             ['presbyopic','hyper','yes','reduced'],  
             ['presbyopic','hyper','yes','normal'],  
            ]
            )'''
    #control.CheckAccuracy('csv','datasets/iris_test')
    #control.CheckAccuracy('csv','datasets/COM_vcpp_c_test')
    #control.DrawTree()
    print(identifyType_db('personal_transcripts_cs',fields=['English','CET4','CET6','AdvancedMath','LinearAlgebra','ProbabilityTheory','DataStructure','DataBase','ComputerNetwork','OperatingSystem','CompositionPrinciple','CppProgramming','ProgrammingPractice','JavaProgramming','CSorSE','NCRE_CPP2']))
    #'COM_MS','COM_VC2','COM_VFP2','COM_SOFT3','NCRE_MS2','NCRE_CPP2','NCRE_NET3'

