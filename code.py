import re
from nltk.stem import PorterStemmer
from xml.etree import cElementTree as ET
from tqdm import tqdm
import math

def tokenization(text):
    """seperate sentence into lower case word tokens """
    regular = r'\w+'
    return re.findall(regular, text.lower())

def removestopwords(text):
    """load the stopwods file and delete the word if it exists in the file"""
    with open('englishST.txt') as f:
        stpwds = f.read().split('\n')
    return [w for w in text if not w in stpwds]

def stemming(text):
    """normolize words"""
    stemmer = PorterStemmer()
    return [stemmer.stem(word) for word in text]

def preprocess(text):
    """tokenize, removestopwords, stemmer the given text"""
    return stemming(removestopwords(tokenization(text)))

def parser():
    """parse the xml string"""
    global total_num
    xmlstr = open('CW1collection/trec.5000.xml').read()
    doc_temp={}
    root= ET.fromstring(xmlstr)
    for arti in root:
        num = arti.find('DOCNO').text
        headline = arti.find('HEADLINE').text
        content = arti.find('TEXT').text
        doc_temp[num] = headline + " " + content
    total_num=len(doc_temp)
    return doc_temp

def index(documents):
    """preprocess the sentences, do the inverted index, store in the nested dic"""
    terms_container={}
    print("making inverted index file...")
    for serial in tqdm(documents):
        terms= preprocess(documents[serial])
        #initialize the first word as 1
        count = 1
        for term in terms:
            if term not in terms_container:
                terms_container[term]={}
            if serial not in terms_container[term]:
                terms_container[term][serial]=[]
                terms_container[term][serial].append(str(count))
            else:
                terms_container[term][serial].append(str(count))
            count+=1
    return terms_container
        
def make_indexfile(terms_container):
    """create the index file and write in the inverted indexes"""
    f = "index.txt"
    for term in sorted(terms_container):
        with open(f, "a+") as file:
            file.write(term + ": " + str(len(terms_container[term])) + "\n")
            for doc in terms_container[term]:
                file.write("\t" + doc + ": " + ",".join(terms_container[term][doc]) + "\n")

def make_boolean_output(terms_container):
    """create the boolean output file and write in the 
    docid of the corresponding queriy"""

    file_boolean="results.boolean.txt"
    q_file=open("CW1collection/queries.boolean.txt")
    queries=q_file.readlines()
    print("making result fot boolean...")
    for index in tqdm(range(len(queries))):
        words=" ".join(queries[index].split(" ")[1:]).rstrip()
        result=searching(words,terms_container)
        for doc in result:
            with open(file_boolean, "a+") as file:
                file.write(str(index+1)+","+str(doc)+"\n")


def multi_terms(term1, term2, dic, distance):
    """doing term indexes for phrases"""
    dicft = dic[term1]
    dicst = dic[term2]
    overlaps = dicft.keys() & dicst.keys()
    result = []
    for page in overlaps:
        contains = False
        ft = [int(x) for x in dicft[page]] #get pos for first term
        st = [int(x) for x in dicst[page]] #get pos for second term
        for p1 in ft:
            if distance > 1:
                for index in range(-distance, distance + 1):
                    if p1 + index in st:
                        contains = True
                        result.append(int(page))
                        break
                if contains:
                    break
            else:
                if p1 + 1 in st:
                    result.append(int(page))
                    break
    return result


def booleanS(left, right, sig_and, sig_or, sig_not):
    global all_list
    all_list = [x for x in range(1, len(terms_container))]
    result = []
    if sig_and == True and sig_not == False:
        result = [x for x in left if x in right]
    elif sig_and == True and sig_not == True:
        result = [x for x in left if x not in right]
    elif sig_or == True and sig_not == False:
        result = list(set(left).union(set(right)))
    elif sig_or == True and sig_not == True:
        result = list(set(left).union(set(all_list).difference(set(right))))
    return result


def single_term(term, dic):
    """doing single term index"""
    result = []
    for key in dic[term]:
        result.append(int(key))
    return result

def special_pre(text):
    """remove characters in the queries and change all terms to lowercase, 
    tokenize them and return the semmed terms"""
    return stemming(tokenization(text))


def searching(queryinput,terms_container):
    left = []
    right = []
    sig_and = False
    sig_or = False
    sig_not = False
    terms = special_pre(queryinput)
    for index in range(len(terms)):
        if "not" not in terms:
            if terms[index] == "and":
                sig_and = True
                left = terms[:index] #contained things at left
                right = terms[index + 1:] #contained things at right
            elif terms[index] == "or":
                sig_or = True
                left = terms[:index]
                right = terms[index + 1:]
        elif terms[index] == "not" :
            sig_not = True
            if index==0:
                if "and" in terms:
                    sig_and = True
                    i = terms.index("and")
                    right = terms[index+1:i]
                    left = terms[i + 1:]
                elif "or" in terms:
                    sig_or = True
                    i = terms.index("or")
                    right = terms[index+1:i]
                    left = terms[i + 1:]
                else:
                    left = terms[index+1:]
            else:               
                if terms[index - 1] == "and":
                    sig_and = True
                    left = terms[:index - 1]
                    right = terms[index + 1:]
                elif terms[index - 1] == "or":
                    sig_or = True
                    left = terms[:index - 1]
                    right = terms[index + 1:]
    if sig_and == False and sig_or == False and sig_not == False:
        if len(terms) == 3:
            distance = int(terms[0].strip("#"))
            result = multi_terms(terms[1], terms[2], terms_container, distance)
        elif len(terms) == 2:
            result = multi_terms(terms[0], terms[1], terms_container, 1)
        elif len(terms) == 1:
            result = single_term(terms[0], terms_container)
    else:
        if sig_and == False and sig_or == False and sig_not == True:
            if len(left) == 1:
                qleft = single_term(left[0], terms_container)
                result = list(set(qleft).difference(set(all_list)))
            elif len(left) == 2:
                qleft = multi_terms(left[0], left[1], terms_container, 1)
                result = list(set(qleft).difference(set(all_list)))
        else:
            if len(left) == 1:
                qleft = single_term(left[0], terms_container)
            else:
                qleft = multi_terms(left[0], left[1], terms_container, 1)
            if len(right) == 1:
                qright = single_term(right[0], terms_container)
            else:
                qright = multi_terms(right[0], right[1], terms_container, 1)
            result = booleanS(qleft, qright, sig_and, sig_or, sig_not)
    result=sorted(result)
    return result

def make_ranked_output(terms_container):
    ranked_file=open("CW1collection/queries.ranked.txt")
    lines=ranked_file.readlines()
    terms=[]
    for line in lines:
        words = preprocess(line)
        terms.append(words)
    score = {}
    print("making result for ranked...")
    for queryindex in tqdm(range(len(terms))):
        score[queryindex] = {}
        for word in terms[queryindex][1:]:
            list_docs = searching(word,terms_container)
            df = len(terms_container[word])
            for arti in list_docs:
                if arti not in score[queryindex]:
                    score[queryindex][arti] = 0
                tf = len(terms_container[word][str(arti)])
                w = (1 + math.log10(tf)) * math.log10(total_num / df)
                score[queryindex][arti] += w
    file_ranked = "results.ranked.txt"
    for queryindex in range(len(terms)):
        for num in sorted(score[queryindex].items(), key=lambda x: (x[1], x[0]), reverse=True)[:150]:
            with open(file_ranked, "a+") as file:
                file.write(str(queryindex + 1) + "," + str(num[0]) + "," + "{:.4f}".format(num[1]) + "\n")

if __name__ == "__main__":
    documents=parser()
    terms_container = index(documents)
    make_indexfile(terms_container)
    make_boolean_output(terms_container)
    make_ranked_output(terms_container)
    print("Task finished.")
