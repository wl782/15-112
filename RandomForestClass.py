import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import random 

class Node: 
    def __init__(self, feature = None, threshold = None, left = None, right = None, value = None):
        self.feature = feature #the features we are taking in 
        self.threshold = threshold #the "threshold" for determining if data goes to right branch or left branch
        self.left = left 
        self.right = right 
        self.value = value  #saves the value only for the leaf node 

class DecisionTree:
    def __init__(self, dataFrame, playerOdd):
        self.root = None  
        self.dataFrame = dataFrame #saves a dataFrame 
        self.playerOdd = playerOdd

    def buildTree(self, dataFrameForPlayer = None):
        if dataFrameForPlayer is None:
            dataFrameForPlayer = self.dataFrame
        if self.playerOdd == 'Over':
            Y = dataFrameForPlayer.iloc[:,-1] #last column (the over) learned from https://www.geeksforgeeks.org/python-extracting-rows-using-pandas-iloc/
        else:
            Y = dataFrameForPlayer.iloc[:,-2] #the one containing the under ones
        if self.sampleIsPure(Y):
            if self.playerOdd == 'Over':
                return Node(value = dataFrameForPlayer['PointsOver'].iat[0]) #base case return leaf Node, with a value for the "value" learned from https://stackoverflow.com/questions/46153647/keyerror-0-when-accessing-value-in-pandas-series
            else:
                return Node(value = dataFrameForPlayer['PointsUnder'].iat[0])
        else:
            bestSample = self.splitSample(dataFrameForPlayer)
            leftTree = bestSample['leftSample']
            rightTree = bestSample['rightSample']
            return Node(bestSample['feature'], bestSample['threshold'], self.buildTree(leftTree), self.buildTree(rightTree))
            #recursive case: split sample, build left and right subtree, return the node with the feature, threshold ..

    def sampleIsPure(self, Y): 
        return len(set(Y)) == 1

    def splitSample(self, dataFrameForPlayer):
        featureRet = rightTreeRet = leftTreeRet = thresholdRet = informationGainRet = None 
        X = dataFrameForPlayer.iloc[:,:-2] #every column except last two https://stackoverflow.com/questions/40144769/how-to-select-the-last-column-of-dataframe 
        for feature in X: #looping through all the columns 
            for threshold in X[feature]: #looping through the values in each column
                leftTree = dataFrameForPlayer[dataFrameForPlayer[feature] < threshold].copy() #getting the rows where it is less than threshold; learned from https://stackoverflow.com/questions/61784255/split-a-pandas-dataframe-into-two-dataframes-efficiently-based-on-some-condition
                rightTree = dataFrameForPlayer[dataFrameForPlayer[feature] >= threshold].copy()
                informationGain = self.informationGainFromSplit(dataFrameForPlayer, leftTree, rightTree)
                if informationGain == None:
                    continue 
                elif informationGainRet == None or informationGain<informationGainRet: #getting the division that gives the most information 
                    featureRet = feature
                    rightTreeRet = rightTree
                    leftTreeRet = leftTree
                    thresholdRet = threshold
        return {'feature':featureRet, 'rightSample': rightTreeRet, 'leftSample': leftTreeRet, 'threshold': thresholdRet} #returning a dictionary (easier to unpack)

    def informationGainFromSplit(self, dataFrameForPlayer, leftTree, rightTree):
        informationGain = self.difference(dataFrameForPlayer, leftTree, rightTree)
        if (informationGain==None):
            return None
        else:
            return informationGain
        
    def difference(self, dataFrameForPlayer, leftTree, rightTree):
        if dataFrameForPlayer.empty or leftTree.empty or rightTree.empty: #handling edge case
            return None
        treeSize= len(dataFrameForPlayer)
        leftTreeSize = len(leftTree)
        rightTreeSize = len(rightTree)
        leftTreeCol = leftTree.iloc[:,-1] #last column (the one with the over/under)
        rightTreeCol = rightTree.iloc[:,-1] #last column (the one with the over/under)
        diffBetweenSamplesLeft = self.diffBetweenSamples(leftTreeCol)
        diffBetweenSamplesRight = self.diffBetweenSamples(rightTreeCol)
        return diffBetweenSamplesLeft*(leftTreeSize/treeSize) + diffBetweenSamplesRight*(rightTreeSize/treeSize) #weighing the differences (so that a 'small' sample doesn't impact the gain too much)

    def diffBetweenSamples(self, dataFrame):
        listOfOnes = []
        listOfZeros = []
        for sample in dataFrame: 
            if sample == 1:
                listOfOnes.append(sample)
            else:
                listOfZeros.append(sample)
        return abs(len(listOfOnes) - len(listOfZeros))
    
    def getMedianRow(self): 
        medianRow = dict()
        newDf = self.dataFrame.replace('-', None) #replacing values with '-', or empty cells, with NaN; learned from https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.replace.html
        for column in newDf.columns:
            columnMedian = []
            for entry in newDf[column]:
                if entry == None:
                    continue 
                else:
                    columnMedian.append(float(entry)) #everything right now is a string
            columnMedian.sort()
            lenOfCol = len(columnMedian)
            if lenOfCol%2==1:
                medianRow[column] = columnMedian[lenOfCol//2]
            else:
                medianRow[column] = (columnMedian[(lenOfCol)//2]+columnMedian[(lenOfCol)//2-1])/2 #get the average of the two middle numbers
        return medianRow  
    
    def predict(self, medianRow, node = None):
        if node is None: #initialize as root node 
            node = self.root
        elif node.value is not None: #if reaches the leaf node, return the value (base case)
            return node.value 
        featureOfRow = medianRow[node.feature]
        if featureOfRow < float(node.threshold):
            return self.predict(medianRow, node.left) #going down the tree 
        else:
            return self.predict(medianRow, node.right) 

#learned how to implement DecisionTree and RandomForest from https://www.youtube.com/watch?v=ZVR2Way4nwQ, https://www.youtube.com/watch?v=NxEHSAfFlK8, https://www.youtube.com/watch?v=kFwe2ZZU7yw, https://www.youtube.com/watch?v=sgQAhG5Q7iY, https://www.youtube.com/watch?v=v6VJ2RO66Ag, and https://www.geeksforgeeks.org/decision-tree-implementation-python/
class RandomForest:
    def __init__(self, nTrees, dataFrame, playerOdd):
        self.nTrees = nTrees
        self.dataFrame = dataFrame
        self.playerOdd = playerOdd
        self.trees = [] 

    def randomSample(self):
        numRows = len(self.dataFrame)
        randomIndices = [random.randint(0,numRows-1) for _ in range(numRows)] 
        return self.dataFrame.iloc[randomIndices] #returns the dataFrame with those randomRows; learned from https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.iloc.html

    def train(self):
        for _ in range (self.nTrees):
            newDataFrame = self.randomSample()
            tree = DecisionTree(newDataFrame, self.playerOdd)
            tree.root=tree.buildTree()
            self.trees.append(tree.predict(tree.getMedianRow()))

    def predict(self):
        numOfOnes = []
        numOfZeroes = []
        for prediction in self.trees:
            if prediction == 1:
                numOfOnes.append(prediction)
            else:
                numOfZeroes.append(prediction)
        lenOfOnes = len(numOfOnes)
        lenOfZeroes = len(numOfZeroes)
        return ((1, lenOfOnes/len(self.trees)) if lenOfOnes > lenOfZeroes else (0, lenOfZeroes/len(self.trees)))





