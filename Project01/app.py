from flask import Flask, render_template, request
from pyltp import Parser
from pyltp import Postagger
from pyltp import Segmentor
from pyltp import SentenceSplitter
import json


LTP_DATA_DIR = '/Users/hang.xiang/Downloads/ltp_data_v3.4.0'


app = Flask(__name__)


@app.route('/')
def hello_world():
    return render_template('form.html')


@app.route('/findwhotalk', methods=['POST'])
def findwhotalk():
    content = request.form['document']
    # print('I get post request:', content)

    wt = Whotalk()
    whodic, markeddoc = wt.checkwhotalk(content, whostart='<strong class="text-danger">', whoend='</strong>', talkstart='<mark>', talkend='</mark>')
    print('get dic:', whodic)

    return '<p>' + markeddoc + '</p>'


class Whotalk:
    def __init__(self, talkwordnum=60):
        # init cut module
        self.segmentor = Segmentor()
        self.segmentor.load(LTP_DATA_DIR + '/cws.model')
        # init postag module
        self.postagger = Postagger()
        self.postagger.load(LTP_DATA_DIR + '/pos.model')
        # init dependency parsing module
        self.parser = Parser()
        self.parser.load(LTP_DATA_DIR + '/parser.model')
        # init talk words
        with open('../saywords.json', 'r') as f:
            self.talkwords = [word for word, score in json.load(f)[:60]]

        print('Whotalk init complete.')

    def istalkindoc(self, doc):
        for talk_w in self.talkwords:
            if talk_w in doc:
                return True
        return False

    def checkwhotalk(self, doc, whostart='', whoend='', talkstart='', talkend=''):
        whodic = {}
        markeddoc = ''

        sentences = SentenceSplitter.split(doc)

        for sentence in sentences:

            if not any([w in sentence for w in self.talkwords]):
                markeddoc += sentence
                continue

            # find all talk words
            words = list(self.segmentor.segment(sentence))
            # for those sentense, get the postag
            postags = self.postagger.postag(words)
            # according to postag get the who and opinion
            arcs = self.parser.parse(words, postags)

            talkindex = -1

            for i, (arc, word) in enumerate(zip(arcs, words)):
                if arc.head == 0 and word in self.talkwords:
                    talkindex = i

            if talkindex == -1:
                markeddoc += sentence
                continue

            who = None, 100

            for word, arc in list(zip(words, arcs))[:i]:
                if arc.relation == 'SBV' and who[1] > arc.head:
                    who = word, arc.head

            whodic[who[0]] = ''.join(words[talkindex + 1:])

            for i, word in enumerate(words):
                if word == who[0] and i < talkindex:
                    markeddoc += whostart + word + whoend
                elif i == talkindex+1:
                    markeddoc += talkstart + word
                else:
                    markeddoc += word
            markeddoc += talkend

        return whodic, markeddoc

    def release(self):
        # release cut module
        self.segmentor.release()
        # release postag module
        self.postagger.release()
        # release dp module
        self.parser.release()

if __name__=="__main__":
    app.run(debug=True)
