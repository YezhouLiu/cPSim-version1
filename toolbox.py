#cP Systems - Yezhou Liu
#toolbox

from copy import deepcopy
from simpleterm import CPSimpleTerm
from compoundterm import CPTerm
from collections import OrderedDict

DETAILS_ON = False
#DETAILS_ON = True

#SIMULATION MODULE - organize it later
def PrintTermDict(dict1):
    for x in dict1:
        print(x.ToString(), ':', dict1[x])
    return True

def ReplaceSimple(_pattern, one_mapping): #use a mapping to eliminate variables in a term/pattern, the mapping does not need to be complete
    pattern = deepcopy(_pattern)
    for m in one_mapping:
        for var in pattern.vars:
            if m == var:
                var_count = pattern.vars[var]
                pattern.value += var_count * one_mapping[m]
                pattern.ConsumeVar(var, var_count)
                break
    return pattern

def ReplaceCompound(_comp_pattern, one_mapping):
    comp_pattern = deepcopy(_comp_pattern)
    for m in one_mapping:
        for var in comp_pattern.vars:
            if m == var:
                var_count = comp_pattern.vars[var]
                comp_pattern.ConsumeVar(var, var_count)
                for term in one_mapping[m]:
                    if term.name == 'value': #value term
                        comp_pattern.value += term.value * var_count
                    else: #subterm
                        comp_pattern.AddSubterm(term, one_mapping[m][term] * var_count)
                break
    if comp_pattern.type == 'COMP':
        new_subterms = OrderedDict()
        for subterm in comp_pattern.subterms:
            new_subterm = ReplaceCompound(subterm, one_mapping)
            new_subterms[new_subterm] = comp_pattern.subterms[subterm]
        new_subterms = OrderedDict(sorted(new_subterms.items()))
        comp_pattern.subterms = new_subterms
    #print(comp_pattern.ToString())
    return comp_pattern

def ReplaceSimpleDict(pattern_dict, one_mapping):
    new_dict = {}
    for x in pattern_dict:
        x1 = ReplaceSimple(x, one_mapping)
        if x1 in new_dict: #important! Both a(X), a(Y), a(Z) can be unified to a(7)! need to accumulate them
            new_dict[x1] += pattern_dict[x]
        else:
            new_dict[x1] = pattern_dict[x]
    return new_dict

def ReplaceCompoundDict(pattern_dict, one_mapping):
    new_dict = {}
    for x in pattern_dict:
        x1 = ReplaceCompound(x, one_mapping)
        if x1 in new_dict:
            new_dict[x1] += pattern_dict[x]
        else:
            new_dict[x1] = pattern_dict[x]
    new_dict = OrderedDict(sorted(new_dict.items()))
    return new_dict

def DictionaryDiff(dict1, dict2, copies_of_dict2 = 1): #do not modify dict1 and dict2
    #assuming dict1 contains dict2
    temp_dict = deepcopy(dict1)
    for x in dict2:
        if x in dict1 and dict1[x] >= dict2[x] * copies_of_dict2:
            temp_dict[x] -= dict2[x] * copies_of_dict2
    return temp_dict

def EliminateDictOverlap(d1, d2):
    dict1 = deepcopy(d1)
    dict2 = deepcopy(d2)
    for x in d1:
        if x in d2:
            if d1[x] > d2[x]:
                dict1[x] -= d2[x]
                dict2.pop(x)
            elif d1[x] < d2[x]:
                dict2[x] -= d1[x]
                dict1.pop(x)
            else:
                dict1.pop(x)
                dict2.pop(x)
    return dict1, dict2

def DictionaryJoin(dict1, dict2): #do not modify dict1 and dict2
    temp_dict = deepcopy(dict1)
    for x in dict2:
        if x in dict1:
            temp_dict[x] += dict2[x]
        else:
            temp_dict[x] = dict2[x]
    return temp_dict

def UnifyCompound(pattern, term):
    if pattern.name != term.name: #do not match a(X) to b(1)
        return []
    elif pattern.IsGround(): #do not need to unify grounded patterns 
        return []
    elif not term.IsGround: #aliasing - illegal in cP systems
        return []
    elif term.type == 'SIMP': #unify simple terms
        all_mappings1 = []
        mapping_dict1 = {}
        UnifyValue(pattern.vars, term.value-pattern.value, mapping_dict1, all_mappings1)
        value_mappings = []
        for x in all_mappings1:
            one_mapping = {}
            for var in x:
                value_term = CPSimpleTerm('value') #pack the value uni to cP compound mapping format
                value_term.value = x[var]
                temp_dict = {}
                temp_dict[value_term] = 1
                one_mapping[var] = temp_dict
            value_mappings.append(one_mapping)
        return value_mappings
    #unify comp terms
    subterm_mappings = []
    UnifyMultiSubterms(pattern, term, subterm_mappings)
    tmp_mappings = deepcopy(subterm_mappings)
    if len(pattern.vars) == 0: #p(m(X)m(Y)m(Z))
        return subterm_mappings
    #else p(P m(X)m(Y)m(Z)) -> still has a P need to unify
    total_mappings = []
    for subm in subterm_mappings:
        all_mappings = []
        new_pattern = ReplaceCompound(pattern, subm) #pattern is not modified
        mapping_dict = {}
        diff = DictionaryDiff(term.subterms, new_pattern.subterms)
        #print(new_pattern.vars)
        UnifyTerm(new_pattern.vars, diff, mapping_dict, all_mappings)
        if term.value > 0:
            all_mappings1 = []
            mapping_dict1 = {}
            UnifyValue(new_pattern.vars, term.value-pattern.value, mapping_dict1, all_mappings1)
            if len(all_mappings) > 0:
                combined_mappings = []
                for x in all_mappings1: #value mappings
                    for y in all_mappings: #subterm mappings
                        one_mapping = {}
                        for var1 in x: #each var1 in a value mapping
                            for var in y: #each var in a subterm mapping y
                                if var1 == var:
                                    temp_dict = deepcopy(y[var])
                                    value_term = CPSimpleTerm('value')
                                    value_term.SetValue(x[var1])
                                    temp_dict[value_term] = 1
                                    one_mapping[var] = temp_dict
                                    break
                        combined_mappings.append(one_mapping)
                for cm in combined_mappings:
                    for m in subm:
                        cm[m] = subm[m]
                total_mappings.extend(combined_mappings)
                continue
        for am in all_mappings:
            for m in subm:
                am[m] = subm[m]
        total_mappings.extend(all_mappings)
    return total_mappings

#No occurs check is needed
def UnifyTerm(_pattern_dict, _term_dict, _shuttle, all_mappings): #mappings: key: X, value: many terms -> subterms -> a dict
    shuttle = deepcopy(_shuttle)
    if len(_pattern_dict) == 0: #a pattern who wants to match subterms, instead of matching its own vars... 
        #go to another pathway, pre-checked
        return False
    first_var = list(_pattern_dict)[0]
    if len(_term_dict) == 0: #for the last variable, basic case of recurision
        for p in _pattern_dict:
            shuttle[p] = {} #empty (ordered) dict
        all_mappings.append(shuttle)
        return True #success 0
    elif len(_pattern_dict) == 1: #a only contains one kind of variable, for example: a(X), a(YY), a(ZZZ)
        for x in _term_dict:
            if _term_dict[x] % _pattern_dict[first_var] > 0:
                return False #cannot unify a(XXX) with a(b(1)b(1))
        temp_dict = {}
        if 'value' in _term_dict: #if considering values
            if _term_dict['value'] % _pattern_dict[first_var] > 0:
                return False
            else:
                value_term = CPSimpleTerm('value')
                value_term.value = _term_dict['value'] / _pattern_dict[first_var]
                temp_dict[value_term] = 1
        for y in _term_dict:
            if _term_dict[y] == 0:
                continue
            y_count = int(_term_dict[y] / _pattern_dict[first_var])
            temp_dict[y] = y_count
        shuttle[first_var] = temp_dict
        all_mappings.append(shuttle)
        return True #success 1
    else:
        magic = [] #a list of tem_list, each element is pissible 'options'
        for t in _term_dict:
            temp_list = [] #a list of dict, key: a term, value: count 
            for i in range(_term_dict[t]+1): #including 0 counts
                if i * _pattern_dict[first_var] > _term_dict[t]:
                    break
                new_dict = {}
                new_dict[t] = i
                temp_list.append(new_dict)
            magic.append(temp_list)
        first_var_unifications = UnifyMagic(first_var, magic)
        for x in first_var_unifications:
            new_pattern_dict = deepcopy(_pattern_dict)
            new_pattern_dict.pop(first_var)
            new_term_dict = DictionaryDiff(_term_dict, x[first_var], _pattern_dict[first_var])
            new_shuttle = DictionaryJoin(shuttle, x)
            UnifyTerm(new_pattern_dict, new_term_dict, new_shuttle, all_mappings)
    return False

def UnifyMagic(one_pattern, magic): #returns a group of dictionaries
    all_unifications = []
    shuttle = {}
    UnifyDifficult(one_pattern, magic, shuttle, all_unifications)
    return all_unifications

def UnifyDifficult(one_pattern, _magic, _shuttle, all_unifications): #compare to unify simple :)
    if len(_magic) == 0:
        new_dict = {}
        new_dict[one_pattern] = deepcopy(_shuttle)
        all_unifications.append(new_dict)
        return True
    x = _magic[0]
    shuttle = deepcopy(_shuttle)
    for y in x:
        for z in y:
            if y[z] == 0:
                continue
            shuttle[z] = y[z] #'decoding' to the dictionary: key: a term, value: count
        magic = deepcopy(_magic[1:])
        UnifyDifficult(one_pattern, magic, shuttle, all_unifications)

def UnifyMultiSubterms(_pattern, _term, all_mappings):
    shuttle = {}
    d1, d2 = EliminateDictOverlap(_pattern.subterms, _term.subterms)
    UnifySubterms(d1, d2, shuttle, all_mappings)

def UnifySubterms(_pattern, _term, _shuttle, all_mappings):
    patterns = deepcopy(_pattern) #dict: term1: 1, term2: 2, term3: 1...
    terms = deepcopy(_term) #dict: term1: 1, term2: 2, term3: 1...
    if len(_pattern) == 0: #success!
        all_mappings.append(_shuttle)
        return True #rest of terms can be used to unify with X, p(X m(Y)m(Z)) - p(m(1)m(2)m(3)m(4)), 2 are used to map Y and Z, other 2 used to map X
    for pat1 in patterns: #one subterm pattern
        pat1_count = patterns[pat1]
        for tm1 in terms: #one subterm
            tm1_count = terms[tm1]
            if pat1_count > tm1_count and tm1.name != 'value': #cannot match p(AAA) to p(a(1)a(1))
                continue
            try_mapping = UnifyCompound(pat1, tm1)
            #print('Try mapping: ', try_mapping)
            if len(try_mapping) > 0: #pat1 can match tm1
                new_patterns = {}
                new_terms = {}
                for one_mapping in try_mapping: #a valid binding(unifier)
                    #replace remain patterns
                    for x in patterns:
                        if x == pat1:
                            continue
                        x1 = ReplaceCompound(x, one_mapping)
                        new_patterns[x1] = patterns[x]
                    #replace remain terms
                    for y in terms:
                        if y == tm1:
                            continue
                        y1 = ReplaceCompound(y, one_mapping)
                        new_terms[y1] = terms[y]
                    shuttle = deepcopy(_shuttle)
                    for m in one_mapping: #copy this valid mapping in shuttle
                        shuttle[m] = one_mapping[m]
                    #print('Shuttle: ', shuttle)
                    UnifySubterms(new_patterns, new_terms, shuttle, all_mappings)
        return False
    return False

def UnifySimple(pattern, term):
    if pattern.name != term.name: #do not match a(X) to b(1)
        return []
    elif pattern.IsGround(): #do not need to unify grounded patterns: a(12), b(7) 
        return []
    elif not term.IsGround: #aliasing: unify a(XY) to a(WZ)
        return []
    elif pattern.value > term.value:
        return [] #cannot match a(3X) with a(2)
    all_mappings = []
    mapping_dict = {}
    #print('The term ', pattern.name, ' contains: ', counting_dict)
    UnifyValue(pattern.vars, term.value-pattern.value, mapping_dict, all_mappings)
    return all_mappings

def UnifyValue(_pattern_dict, value, _mapping_dict, all_mappings): #a(XYYZZZZ) - pattern_dict: {'X':1, 'Y':2, 'Z':4}
    pattern_dict = deepcopy(_pattern_dict)
    mapping_dict = deepcopy(_mapping_dict)
    if len(pattern_dict) == 0: #it should not happen
        return False
    first_var = list(pattern_dict)[0]
    if value < 0: #it should not happen
        return False
    if value == 0: #mapping a(XXYZ) with a(0), get X=Y=Z=0
        for p in pattern_dict:
            mapping_dict[p] = 0
        all_mappings.append(mapping_dict)
        return True #success 0
    elif len(pattern_dict) == 1: #a only contains one kind of variable, for example: a(X), a(YY), a(ZZZ)
        if value % pattern_dict[first_var] > 0:
            return False #cannot unify a(XXX) with a(7)
        else:
            mapping_dict[first_var] = int(value / pattern_dict[first_var]) #mapping a(XXX) with a(6), get X=2
            all_mappings.append(mapping_dict)
            return True #success 1
    else:
        for i in range(value+1):
            if i * pattern_dict[first_var] > value:
                break #think about it...
            new_value = value - i * pattern_dict[first_var]
            mapping_dict_copy = deepcopy(mapping_dict)
            mapping_dict_copy[first_var] = i
            pattern_dict_copy = deepcopy(pattern_dict)
            pattern_dict_copy.pop(first_var)
            UnifyValue(pattern_dict_copy, new_value, mapping_dict_copy, all_mappings)
    return False

#debug functions
def PrintUnifyCompound(x):
    if not DETAILS_ON:
        return
    for y in x:
        print('--------------')
        for z in y:
            s = ''
            for w in y[z]:
                s += (' ' + w.ToString() ) * y[z][w]
            print(z, ':', s)
    print('--------------')

def SelectPrint(x):
    if not DETAILS_ON:
        return
    print(x)