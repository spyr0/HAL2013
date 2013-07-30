'''
A set of value domains
Created on 7 août 2011
@author: stephane
'''
__all__ = ["Interval","ValueSet", "TagSet"]
import abc

class AbstractValueDomain(metaclass=abc.ABCMeta):
    '''
    Abstract class specifying what is a domain
    '''
    @abc.abstractmethod
    def contains(self):
        raise NotImplementedError()
    @abc.abstractmethod
    def display(self):
        raise NotImplementedError()
    
class Interval(AbstractValueDomain):
    '''
    Domain corresponding to a mathematical interval (for real numbers)
    '''
    def __init__(self,min,max):
        self.min=min
        self.max=max
    def contains(self,value):
        return float(value)>=self.min and float(value)<=self.max
    def display(self):
        return "<domain><type>Interval</type><min>%f</min><max>%f</max></domain>"%(self.min,self.max)

class ValueSet(AbstractValueDomain):
    '''
    Domain corresponding to a set of values: the values are converted into tags (string litterals)
    '''
    def __init__(self,possibleValues):
        self.possibleValues=possibleValues
        self.tags=list()
        for value in possibleValues:
            self.tags.append(str(value))
    def contains(self,value):
        return value in self.possibleValues
    def display(self):
        return "<domain><type>ValueSet</type><value>"+"</value><value>".join(self.tags)+"</value></domain>"
    
class TagSet(AbstractValueDomain):
    '''
    Domain corresponding to a set of tags
    '''
    def __init__(self,possibleTags):
        self.possibleTags=possibleTags
    def contains(self,value):
        return value in self.possibleTags
    def display(self):
        return "<domain><type>TagSet</type><value>"+"</value><value>".join(self.possibleTags)+"</value></domain>"

if __name__ == '__main__':
    interval=Interval(2,5)
    print(interval.contains(3))
    print(interval.contains(7))
    print(interval.contains('a'))
    print(interval.display())
    valueSet=ValueSet((2,4.5,8,9))
    print(valueSet.contains(8))
    print(valueSet.contains(4.5))
    print(valueSet.contains(2))
    print(valueSet.contains(8.5))
    print(valueSet.contains('ab'))
    print(valueSet.display())
    tagSet=TagSet(('on','off','average','.7'))
    print(tagSet.contains('on'))
    print(tagSet.contains('o'))
    print(tagSet.contains(.7))
    print(tagSet.display())