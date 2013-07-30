#!/usr/bin/python2.6
'''
Created on 26 May 2010
@author: Shadi

'''

class TrameDividing(): #To divide frames

    def __init__(self, frames):
        self.internalFrames = frames
        #dictionary {"label":length}
        #temperature = {"50":33}, power = {"30":21} , x10 (battery) = {"20":15}
        self.tramDictionnary = {"50":32, "30":20, "20":14}
        
    def checkCompletTram(self, index):
        tramDictionnary = self.tramDictionnary
        frames = self.internalFrames
        isCompletTram = False
        #on cherche si la trame courante est complete, cela veut dire que la trame suivante commence par un des labels
        if index < len(frames):
            for label, length in tramDictionnary.items():
                if not isCompletTram:
                    if frames[index: index+2] ==label:
                        isCompletTram = True
                        break
                else:
                    break
            #else:
                    #print "Sorry, it is not a complete tram"
        elif index == len(frames):
            isCompletTram = True
        return  isCompletTram
    
    # on cherche le debut de la trame suivante
    def searchNextCompletTramIndex(self,currentIndex):
        index = currentIndex
        tramDictionnary = self.tramDictionnary
        frames = self.internalFrames
        nextLabelIsFound = False
        while index < len(frames) and not nextLabelIsFound:
            index= index+1
            for label, length in tramDictionnary.items():
                nextLabelIsFound = self.checkCompletTram(index)
                if nextLabelIsFound:
                    break        
        return index 
            
    def dividing(self):
        tramDictionnary = self.tramDictionnary
        frames = self.internalFrames
        seperatedFrames =[]
        index = 0
        StepLength = 0
        while index < len(frames):
            for label, length in tramDictionnary.items():
                if frames[index: index+2] ==label:
                    isCompletTram = self.checkCompletTram(index+length)
                    if isCompletTram:
                        trame = frames[index:index+length]
                        seperatedFrames.append(trame)
                        print(trame)
                        StepLength = length
                        break
                    else:
                        index = self.searchNextCompletTramIndex(index+1)
                        StepLength = 0
                        break
            else:
                print("Sorry, it is not a trame")
                index=len(frames)
            index = index + StepLength
            
        return seperatedFrames
    