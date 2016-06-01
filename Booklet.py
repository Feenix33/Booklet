# 001 Class to figure out measurements for frames (not real frames)
# 002 Update fake frame class to be more self contained (temp hold platypus stuff)
# 003 Columns approach
# 004 Refactor 003 to use a Frame Generator; removed simple box layout 
# 005 Create styles
# 006 Gutters 
# 007 Use a generic layout common to horiz and vertical
# 008 Use parameters in the class instead of passing them all over
# 009 Clean up some of the subroutines and make them more concise
# 010 read data from a file; use default file and argument passed file name
#     pass along different font sizes for the default type
# 011 Move argument processing to its own routines
#
# different types of file: text, text w/blank lines as new para, 
# file types: list, simple instructions 
# titles
# arguments to pass:
#    paragraph spacing
#    put in arg proc in own routine


# row and column backward, need to test all the parameters
# try logging vs printing

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

    if (not os.path.isfile(theArgs.infile)):
      print ("Input file {} does not exist".format(theArgs.infile))
      exit()


class Booklet():
  def __init__(self, pdfFile, layoutConfig): 
    self.doc = BaseDocTemplate(filename=pdfFile, showBoundary=1, pagesize=layoutConfig.pagesize)
    self.docHeight = self.doc.pagesize[1]
    self.docWidth  = self.doc.pagesize[0]
    self.defaultStyle = ParagraphStyle('defaultStyle')
    self.defaultStyle.fontSize = layoutConfig.fontSize
    self.defaultStyle.leading = layoutConfig.leading 
    self.defaultStyle.fontName = layoutConfig.fontName

    self.titleStyle = ParagraphStyle('titleStyle')
    self.titleStyle.fontSize = 10
    self.titleStyle.leading = 12
    self.titleStyle.alignment = TA_LEFT

    self.numHorz = layoutConfig.cols
    self.numVert = layoutConfig.rows

    self.gutterH = layoutConfig.gutterH
    self.gutterV = layoutConfig.gutterV
    self.marginH = layoutConfig.marginH
    self.marginV = layoutConfig.marginV
    self.pageTypeH = layoutConfig.pageTypeH
    self.pageTypeV = layoutConfig.pageTypeV
  
  def setFontFamily(self, index):
    if index <= 0:
      self.defaultStyle.fontName = "Courier"
    elif index == 1:
      self.defaultStyle.fontName = "Helvetica"
    else:
      self.defaultStyle.fontName = "Times-Roman"

  def setRowCol(self, rows=0, cols=0):
    if rows != None and rows > 0:
      self.numHorz = rows
    if cols != None and cols > 0:
      self.numVert = cols

  def setBodyFont(self, size):
    if size < 1:
      self.defaultStyle.fontSize = 8
    self.defaultStyle.fontSize = size
    self.defaultStyle.leading = int(self.defaultStyle.fontSize * 1.25 + 0.5)
    #self.titleStyle.leading = int(self.defaultStyle.fontSize * 1.25 + 0.5)


  def divisions(self, totalWidth, numFrames, margin, gutter, useType):
    # take the totalWidth and divide it into the number of frames based on the type
    # can be horz or vert, but use horz terms
    # 1 no gutter   |mm ffff mm  mm ffff mm  mm ffff mm  mm ffff mm|
    # 1 use gutter  |mm ffff mm  gg FFFF gg  gg FFFF gg  mm ffff mm|
    # 2 max use     |mm ffff gg  gg FFFF gg  gg FFFF gg  gg ffff mm|
    columnWidth = totalWidth / numFrames

    #debug
    print ("type margin gutter = ", useType, margin, gutter)

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


  def Build(self, elements):
    self.doc.build(elements)

def main():
  pdfFile = __file__[:-2] + "pdf"
  if (os.path.isfile(pdfFile)):
    os.remove(pdfFile)
  # 0, 0 is bottom left
  # dim is 612, 792 or 72=inch

  myLayout = LayoutConfiguration()
  myLayout.SetupParser()
  myLayout.ProcessArgs()

  inFile = open(myLayout.infile, "r")

  book = Booklet(pdfFile, myLayout)


  book.layout() #book.numHorz, book.numVert)

  Elements=[]
  styles=getSampleStyleSheet()

  for inLine in inFile:
    Elements.append(Paragraph(inLine, book.defaultStyle))

  book.Build(Elements)


if __name__ == '__main__':
  main()
