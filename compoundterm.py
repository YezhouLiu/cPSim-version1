#cP Systems - Yezhou Liu
#compound term

from simpleterm import CPSimpleTerm
from collections import OrderedDict

class CPTerm(CPSimpleTerm): 
    def __init__(self, name, vars = '', value = 0):
        CPSimpleTerm.__init__(self, name, value, vars)
        self.subterms = OrderedDict()

    def __eq__(self, term2): 
        if not isinstance(term2, CPTerm): #only compare comp terms
            return False
        return self.ToString() == term2.ToString()

    def __lt__(self, term2): #less than
        return self.ToString() < term2.ToString()

    def __hash__(self): #implement eq and hash function, which the system can use CPTerm as a dictionary key
        return hash(self.ToString())

    def AddSubterm(self, term, count = 1): #when adding subterms, make sure the dict is ordered, which will be used later in the hash function
        if term in self.subterms:
            self.subterms[term] += count
        else:
            self.subterms[term] = count
        self.subterms = OrderedDict(sorted(self.subterms.items()))
        self.UpdateType()
        return True

    def UpdateType(self):
        if len(self.subterms) == 0:
            self.type = 'SIMP'
        else:
            self.type = 'COMP' 

    def ConsumeSubterm(self, term):
        if not term in self.subterms:
            print('Error e3!')
            return False
        if self.subterms[term] > 1:
            self.subterms[term] -= 1
        else:
            self.subterms.pop(term)
        self.UpdateType()
        return True

    def ToString(self):
        temp_str = self.name + '('
        if len(self.vars) > 0:
            for var in sorted(self.vars):
                for _ in range(0, self.vars[var]):
                    temp_str += var
        for term in self.subterms:
            for _ in range(self.subterms[term]): #count
                temp_str += term.ToString() #comp term subterms
        if self.value > 0:
            temp_str += str(self.value)
        temp_str += ')'
        return temp_str

    def IsGround(self):
        term_str = self.ToString()
        for i in range(len(term_str)):
            if term_str[i] >= 'A' and term_str[i] <= 'Z':
                return False
        return True

