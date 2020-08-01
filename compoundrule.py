#cP Systems - Yezhou Liu
#compound rule

from compoundterm import CPTerm

class CPRule:
    def __init__(self, sl = '', sr = '', model = '1'):
        self.state_l = sl
        self.state_r = sr
        self.lhs = {} #terms in lhs
        self.rhs = {} #terms in rhs
        self.pmt = {}
        self.model = model # '1' exact-once, '+' max-parallel

    def IsGround(self): #rule consists of grounded terms only
        if not self.IsValid():
            return False
        for x in self.lhs:
            if not x.IsGround():
                return False
        for y in self.pmt:
            if not y.IsGround():
                return False
        return True

    def ToString(self):
        temp_str = self.state_l + ' '
        for x in self.lhs:
            x_count = self.lhs[x]
            for _ in range(0, x_count):
                temp_str += x.ToString() + ' '
        temp_str += '->' + self.model + ' '
        temp_str += self.state_r + ' '
        for y in self.rhs:
            y_count = self.rhs[y]
            for _ in range(0, y_count):
                temp_str += y.ToString() + ' '
        if len(self.pmt) > 0:
            temp_str += '| '
            for z in self.pmt:
                z_count = self.pmt[z]
                for _ in range(0, z_count):
                    temp_str += z.ToString() + ' '
        return temp_str

    def SetStates(self, sl, sr):
        self.state_l = sl
        self.state_r = sr
        return True

    def AddL(self, term):
        if term in self.lhs:
            self.lhs[term] += 1
        else:
            self.lhs[term] = 1
        return True

    def AddR(self, term):
        if term in self.rhs:
            self.rhs[term] += 1
        else:
            self.rhs[term] = 1
        return True

    def AddPM(self, term):
        if term in self.pmt:
            self.pmt[term] += 1
        else:
            self.pmt[term] = 1
        return True

    def IsValid(self): #to avoid rules like: a(1) ->1 a(X) -- a variable appears in rhs, must appear in lhs first (or in promoters)
        variables_set = {''}
        lp_str = ''
        for term in self.lhs:
            lp_str += term.ToString()
        for term in self.pmt:
            lp_str += term.ToString()
        for i in range(len(lp_str)):
            if lp_str[i] >= 'A' and lp_str[i] <= 'Z':
                variables_set.add(lp_str[i])
        r_str = ''
        for term in self.rhs:
            r_str += term.ToString()
        for i in range(len(r_str)):
            if r_str[i] >= 'A' and r_str[i] <= 'Z':
                if not r_str[i] in variables_set:
                    return False
        return True