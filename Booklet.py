from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen.canvas import Canvas  # check
from reportlab.lib.colors import *  # check
import os.path

import inspect, os
import argparse
import random  # check


from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import BaseDocTemplate, Frame, Paragraph, PageTemplate
from reportlab.platypus import Spacer, FrameBreak, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import *


class LayoutConfiguration():
  def __init__(self):
    self.gutterH = 8
    self.gutterV = 8
    self.numHorz = 4
    self.numVert = 2
    self.marginH = 72 / 3
    self.marginV = 72 / 2
    self.pageTypeH = 2
    self.pageTypeV = 2
    self.parser = argparse.ArgumentParser()
    self.pagesize = letter
    self.fontSize = 8
    self.leading = 10
    self.fontName = "Helvetica"
    self.rows = 1
    self.cols = 1
    self.infile = "in.txt"
    self.fileparser = 0

  def SetupParser(self):
    self.parser.add_argument("infile", nargs='?',default="in.txt",
      help="input file to process (defaults to in.txt")
    self.parser.add_argument("-fs", "--fontsize", type=int,
      help="Specify the base font size")
    self.parser.add_argument("-ff", "--fontfamily", type=int,
      help="Specify the font family 0=Courier 1=Helvetica 2=Times-Roman")
    self.parser.add_argument("-l", "--landscape", action="store_true", 
      help="Use landscape layout")
    self.parser.add_argument("-r", "--rows", type=int,
      help="Specify the number of row frames")
    self.parser.add_argument("-c", "--cols", type=int,
      help="Specify the number of col frames")
    self.parser.add_argument("-mh", "--marginhorz", type=int,
      help="Margin in points for the horizontal direction where 1 inch = 72 points")
    self.parser.add_argument("-mv", "--marginvert", type=int,
      help="Margin in points for the vertical direction where 1 inch = 72 points")
    self.parser.add_argument("-ph", "--pagetypehorz", type=int,
      help="Horizontal pagetype (0=margins only 1=margin+gutter 2=max, gutters only")
    self.parser.add_argument("-pv", "--pagetypevert", type=int,
      help="Vertical pagetype (0=margins only 1=margin+gutter 2=max, gutters only")
    self.parser.add_argument("-gh", "--gutterhorz", type=int,
      help="Horizontal gutter width in points (1 inch = 72 points")
    self.parser.add_argument("-gv", "--guttervert", type=int,
      help="Vertical gutter width in points (1 inch = 72 points")
    self.parser.add_argument("-fp", "--fileparser", type=int,
      help="File parser type 0=line 1=compact 2=Croff")

  def ProcessArgs(self):
    theArgs = self.parser.parse_args()
    if theArgs.fontsize:
      if theArgs.fontsize > 0:
        self.fontSize = theArgs.fontsize
        self.leading = int(self.fontSize * 1.25 + 0.5)

    if theArgs.fontfamily:
      if theArgs.fontfamily <= 0:
        self.fontName = "Courier"
      elif theArgs.fontfamily == 1:
        self.fontName = "Helvetica"
      else:
        self.fontName = "Times-Roman"

    if theArgs.landscape:
      self.pagesize = landscape(letter)

    if theArgs.rows and theArgs.rows > 0:
      self.rows = theArgs.rows
    if theArgs.cols and theArgs.cols > 0:
      self.cols = theArgs.cols

    if theArgs.marginhorz and theArgs.marginhorz > 0:
        self.marginH = theArgs.marginhorz 

    if theArgs.marginvert and theArgs.marginvert > 0:
        self.marginV = theArgs.marginvert 

    if theArgs.pagetypehorz and theArgs.pagetypehorz > 0:
        self.pageTypeH = theArgs.pagetypehorz 

    if theArgs.pagetypevert and theArgs.pagetypevert > 0:
      self.pageTypeV = theArgs.pagetypevert 

    if theArgs.gutterhorz and theArgs.gutterhorz > 0:
      self.gutterH = theArgs.gutterhorz 

    if theArgs.guttervert and theArgs.guttervert > 0:
      self.gutterV = theArgs.guttervert 

    if theArgs.fileparser and theArgs.fileparser > 0:
      self.fileparser = theArgs.fileparser 

    if (not os.path.isfile(theArgs.infile)):
      print ("Input file {} does not exist".format(theArgs.infile))
      exit()
    else:
      self.infile = theArgs.infile


class Booklet():
  def __init__(self, pdfFile, layoutConfig): 
    self.doc = BaseDocTemplate(filename=pdfFile, showBoundary=1, pagesize=layoutConfig.pagesize)
    self.docHeight = self.doc.pagesize[1]
    self.docWidth  = self.doc.pagesize[0]
    self.defaultStyle = ParagraphStyle('defaultStyle')
    self.defaultStyle.fontSize = layoutConfig.fontSize
    self.defaultStyle.leading = layoutConfig.leading 
    self.defaultStyle.fontName = layoutConfig.fontName
    #self.defaultStyle.spaceAfter = 6

    self.titleStyle = ParagraphStyle('titleStyle')
    self.titleStyle.fontSize = 10
    self.titleStyle.leading = 12
    self.titleStyle.spaceBefore = 6
    self.titleStyle.spaceAfter = 6
    self.titleStyle.alignment = TA_CENTER

    self.numHorz = layoutConfig.cols
    self.numVert = layoutConfig.rows

    self.spacerSize = layoutConfig.fontSize

    self.gutterH = layoutConfig.gutterH
    self.gutterV = layoutConfig.gutterV
    self.marginH = layoutConfig.marginH
    self.marginV = layoutConfig.marginV
    self.pageTypeH = layoutConfig.pageTypeH
    self.pageTypeV = layoutConfig.pageTypeV
    self.fileparser = layoutConfig.fileparser  # don't like this duplication
  
    self.elements=[]
    self.mode = 0
    self.para = ''
    self.paraStyle = self.defaultStyle


  def divisions(self, totalWidth, numFrames, margin, gutter, useType):
    # take the totalWidth and divide it into the number of frames based on the type
    # can be horz or vert, but use horz terms
    # 1 no gutter   |mm ffff mm  mm ffff mm  mm ffff mm  mm ffff mm|
    # 1 use gutter  |mm ffff mm  gg FFFF gg  gg FFFF gg  mm ffff mm|
    # 2 max use     |mm ffff gg  gg FFFF gg  gg FFFF gg  gg ffff mm|
    columnWidth = totalWidth / numFrames

    #debug print ("type margin gutter = ", useType, margin, gutter)

    if (numFrames == 1 or useType == 0):
      #case 0 no gutter, left is alwas margin, widths are all the same
      lefts = [i*columnWidth+margin  for i in range(numFrames)]
      widths = [columnWidth-2*margin for i in range(numFrames)]

    elif (useType == 1):
      #case 1 use gutter, first and last same, middle different
      #first make everything use gutters
      lefts = [i*columnWidth+gutter  for i in range(numFrames)]
      widths = [columnWidth-2*gutter for i in range(numFrames)]
      #adjust first and last
      lefts[0] = lefts[0] - gutter + margin
      lefts[-1] = lefts[-1] - gutter + margin
      widths[0] = columnWidth - 2*margin
      widths[-1] = widths[0]

    else: #useType == 2
      #case 2 use gutter, first and last same, middle different
      #first make everything use gutters
      lefts = [i*columnWidth+gutter  for i in range(numFrames)]
      widths = [columnWidth-2*gutter for i in range(numFrames)]
      #adjust first and last
      lefts[0] = lefts[0] - gutter + margin
      widths[0] = columnWidth - margin - gutter
      widths[-1] = widths[0]

    return lefts, widths


  def layout(self):
    frames = []

    frameLeft, frameWidth = self.divisions(self.docWidth, self.numHorz, self.marginH, self.gutterH, self.pageTypeH)
    frameTop, frameHeight = self.divisions(self.docHeight, self.numVert, self.marginV, self.gutterV, self.pageTypeV)

    for vert in range(self.numVert-1, -1, -1):
      for horz in range(self.numHorz):
        frames.append(Frame(frameLeft[horz], frameTop[vert], frameWidth[horz], frameHeight[vert]))

    self.doc.addPageTemplates([PageTemplate(id='myFrame',frames=frames)])

  def parseSimple(self, inFileName):
    #every line is a paragraph
    inFile = open(inFileName, "r")
    Elements=[]
    for inLine in inFile:
      Elements.append(Paragraph(inLine, self.defaultStyle))
    return Elements;

  def parseLines(self, infile):
    # new paragraph when we see an empty line
    # multiples get automatically ignored
    # cannnot force empty paragraphs w/spaces or carriage returns
    # don't have to worry about the end
    Elements=[]
    para=''
    with open(infile) as f:
      for inLine in f.read().splitlines():
        if len(inLine) == 0:
          Elements.append(Paragraph(para, self.defaultStyle))
          para=''
        else:
          para += inLine
    Elements.append(Paragraph(para, self.defaultStyle)) #for end of file
    return Elements;

  def parseCroff(self, infile):
    self.mode = 0 # 0 fill, 1 list, 2 title
    self.para=''
    with open(infile) as f:
      for inLine in f.read().splitlines():
        if len(inLine) > 0 and inLine[0] == '.':
          self.processCommand(inLine)
        else:
          self.processData(inLine)
    if self.para != '':  #end of file, flush our remaining
      self.elements.append(Paragraph(para, self.defaultStyle))
      self.para = ''
    return self.elements;

  def processCommand(self, line):
    #anytime there is a new command, check to clear our paragraph
    if self.para != '':
      self.elements.append(Paragraph(self.para, self.defaultStyle))
      self.para = ''
    # switch statement through the commands
    token = line.split()
    if token[0] == ".fi":
      self.mode = 0 #fill
    elif token[0] == ".li" :
      self.mode = 1 #list
    elif token[0] == ".ti" :
      self.mode = 2 #title
    elif token[0] == ".nl" :
      self.mode = 3 #numbered list
    elif token[0] == ".nr" : # reset number
      self.elements.append(Paragraph("<seqreset id='spam'", self.defaultStyle))
      self.mode = 3 
    elif token[0] == ".sp" :
      if len(token) > 1 and token[1].isdigit():
        times = int(token[1])
      else:
        times = 1
      for j in range(times):
        self.elements.append(Spacer(1, self.spacerSize)) 
    elif token[0] == ".nf" :
      self.elements.append(FrameBreak())
    elif token[0] == ".np" :
      self.elements.append(PageBreak())
    else:
      print ("Error Command " + token[0])


  def processData(self, line):
    self.para += line
    if self.mode == 2:
      self.para = "<b>" + self.para + "</b>"
      self.elements.append(Paragraph(self.para, self.titleStyle))
      self.para = ''
    elif self.mode == 3:
      if self.para != '':
        self.para = "<seq id='spam'/> " + self.para
        self.elements.append(Paragraph(self.para, self.defaultStyle))
        self.para = ''
    elif self.mode == 1: 
      self.elements.append(Paragraph(self.para, self.defaultStyle)) 
      self.para = ''
    else:
      if len(line) == 0:
        self.elements.append(Spacer(1, self.spacerSize))
        self.elements.append(Paragraph(self.para, self.defaultStyle)) #for end of file
        self.para = ''

  def Build(self, inFile):
    if self.fileparser == 0:
      self.doc.build(self.parseSimple(inFile))
    elif self.fileparser == 1:
      self.doc.build(self.parseLines(inFile))
    elif self.fileparser == 2:
      self.doc.build(self.parseCroff(inFile))

def main():
  pdfFile = __file__[:-2] + "pdf"
  if (os.path.isfile(pdfFile)):
    os.remove(pdfFile)
  # 0, 0 is bottom left
  # dim is 612, 792 or 72=inch

  myLayout = LayoutConfiguration()
  myLayout.SetupParser()
  myLayout.ProcessArgs()

  #inFile = open(myLayout.infile, "r")

  book = Booklet(pdfFile, myLayout)
  book.layout()
  #book.Build(inFile)
  book.Build(myLayout.infile)


if __name__ == '__main__':
  main()
