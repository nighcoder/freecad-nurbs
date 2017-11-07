# -*- coding: utf-8 -*-
'''interactive drawing of a curve onto a face'''
#-------------------------------------------------
#-- interctive draw on face
#--
#-- microelly 2017  0.2
#--
#-- GNU Lesser General Public License (LGPL)
#-------------------------------------------------


##\cond
from PySide import QtGui,QtCore
from nurbswb.say import *

import FreeCAD
import sys,time
import random



import nurbswb.isodraw
reload(nurbswb.isodraw)



'''
# parameter
FreeCAD.ParamGet('User parameter:Plugins/nurbs').GetFloat("MoveWheelStep",1)
FreeCAD.ParamGet('User parameter:Plugins/nurbs').GetFloat("MovePageStep",50)
FreeCAD.ParamGet('User parameter:Plugins/nurbs').GetFloat("MoveCursorStep",10)

'''


##\endcond

## Eventfilter for facedrawing

class EventFilter(QtCore.QObject):
	'''Eventfilter for facedrawing'''

##\cond

	def __init__(self):
		QtCore.QObject.__init__(self)
		self.mouseWheel=0
		self.enterleave=False
		self.enterleave=True
		self.keyPressed2=False
		self.editmode=False
		self.key='x'
		self.posx=-1
		self.posy=-1
		self.lasttime=time.time()
		self.lastkey='#'
		self.colorA=0
		self.colors=[]
		self.pts=[]
		self.ptsm=[]
		self.mode='n'

	def eventFilter(self, o, e):
		''' the eventfilter for the facedraw server'''

		z=str(e.type())

		event=e

		if event.type() == QtCore.QEvent.ContextMenu : return True

		# not used events
		if z == 'PySide.QtCore.QEvent.Type.ChildAdded' or \
				z == 'PySide.QtCore.QEvent.Type.ChildRemoved'or \
				z == 'PySide.QtCore.QEvent.Type.User'  or \
				z == 'PySide.QtCore.QEvent.Type.Paint' or \
				z == 'PySide.QtCore.QEvent.Type.LayoutRequest' or\
				z == 'PySide.QtCore.QEvent.Type.UpdateRequest'  : 
			return QtGui.QWidget.eventFilter(self, o, e)

		if event.type() == QtCore.QEvent.MouseMove:
				(x,y)=Gui.ActiveDocument.ActiveView.getCursorPos()
				t=Gui.ActiveDocument.ActiveView.getObjectsInfo((x,y))

				if t<>None: # if objects are under the mouse
					for tt in t:
						if tt['Object']==self.objname and tt['Component']==self.subelement:
							self.x,self.y,self.z=tt['x'],tt['y'],tt['z']
							break

					if event.buttons()==QtCore.Qt.LeftButton:
						#print "LEFT BUTTON drawing"
						vf=FreeCAD.Vector(self.x,self.y,self.z)
						bs=self.subobj.Surface

						(u,v)=bs.parameter(vf)
						#print (u,v)
						lu=0.5
						lv=0.5

						ba=bs.vIso(u)
						ky=ba.length(v,lv)
						if v<0.5: ky =-ky

						bbc=bs.vIso(v)
						kx=bbc.length(lu,u)
						if u<0.5: kx =-kx

						mf=FreeCAD.Vector(self.x,self.y,0)
						mf=FreeCAD.Vector(-1*ky,-1*kx,0)

						self.pts += [vf]
						self.ptsm += [mf]

						self.colors += [self.colorA]
						drawColorpath(self.pts,self.colors,self.colorA)
						self.wire.ViewObject.Visibility=False

						if len(self.pts)>1:
							self.wire.Shape=Part.makePolygon(self.pts)
							self.wirem.Shape=Part.makePolygon(self.ptsm)

						return True

		if z == 'PySide.QtCore.QEvent.Type.KeyPress':
			# http://doc.qt.io/qt-4.8/qkeyevent.html

			# ignore editors
			try:
				if self.editmode:
					return QtGui.QWidget.eventFilter(self, o, e)
			except: pass

			# only first time key pressed
			if not self.keyPressed2:
				self.keyPressed2=True
				time2=time.time()
				ee=e.text()

				if time2-self.lasttime<0.01 and len(ee)>0 and ee[0]==self.lastkey:
					self.lasttime=time2
					return False

				try:
					# only two function keys implemented, no modifieres
					if e.key()== QtCore.Qt.Key_F2:
						say("------------F2-- show mode and moddata---------------")
						return False

					elif e.key()== QtCore.Qt.Key_Escape:
						say("------------Escape = Stop-----------------")
						stop()

					elif e.key()== QtCore.Qt.Key_F3 :
						say("------------F3-----------------")
						stop()


# some key bindings not used at teh moment
#					elif  e.key()== QtCore.Qt.Key_Return:
#						say("------------Enter-----------------")
#						self.update()
					elif e.key() == QtCore.Qt.Key_Right :
						if self.dialog.dial.value()==self.dialog.dial.maximum(): val=0
						else: val=self.dialog.dial.value()+1
						self.dialog.dial.setValue(val)
						return True
					elif e.key() == QtCore.Qt.Key_Left :
						if self.dialog.dial.value()== 0: val=self.dialog.dial.maximum()
						else: val=self.dialog.dial.value()-1
						self.dialog.dial.setValue(val)
						return True
					elif e.key() == QtCore.Qt.Key_Up :
						self.mouseWheel += FreeCAD.ParamGet('User parameter:Plugins/nurbs').GetFloat("MoveCursorStep",10)
						self.dialog.ef_action("up",self,self.mouseWheel) 
						return True
					elif e.key() == QtCore.Qt.Key_Down :
						self.mouseWheel -= FreeCAD.ParamGet('User parameter:Plugins/nurbs').GetFloat("MoveCursorStep",10) 
						self.dialog.ef_action("down",self,self.mouseWheel)
						return True
					elif e.key() == QtCore.Qt.Key_PageUp :
						self.mouseWheel += FreeCAD.ParamGet('User parameter:Plugins/nurbs').GetFloat("MovePageStep",50)
						self.dialog.ef_action("up!",self,self.mouseWheel)
						return True
					elif e.key() == QtCore.Qt.Key_PageDown :
						self.mouseWheel -= FreeCAD.ParamGet('User parameter:Plugins/nurbs').GetFloat("MovePageStep",50)
						self.dialog.ef_action("down!",self,self.mouseWheel)
						return True

					if e.key()== QtCore.Qt.Key_Enter or e.key()== QtCore.Qt.Key_Return:
						# enter creates a new point ...
						vf=FreeCAD.Vector(self.x,self.y,self.z)
						self.colors += [self.colorA]
						self.pts += [vf]

						if len(self.pts)>1:
							self.wire.Shape=Part.makePolygon(self.pts)
							drawColorpath(self.pts,self.colors,self.colorA)

					else: # letter key pressed
						ee=e.text()
						if len(ee)>0: r=ee[0]
						else: r="key:"+ str(e.key())

						self.lastkey=e.text()

						#color select for drawing
						if r=='h':
							self.colorA=0
							return True
						if r=='y':
							self.colorA=1
							return True
						if r=='n':
							self.colorA=2
							return True
						if r=='g':
							self.colorA=3
							return True
						if r=='j':
							self.colorA=4
							return True
						if r=='z':
							self.colorA=6
							return True
						if r=='x':
							self.colorA=5
							return True
						if r=='#':
							self.colorA=7
							return True

						# zooming +-*
						if r=='+':
							Gui.activeDocument().ActiveView.zoomIn()
							return True
						if r=='-':
							Gui.activeDocument().ActiveView.zoomOut()
							return True
						if r=='*':
							Gui.activeDocument().ActiveView.fitAll()
							return True


 						if r in ['a','b','c']:

								print ("KEY pressed ----------------------",r)



				except:
					sayexc()


		# end of a single key pressed
		if z == 'PySide.QtCore.QEvent.Type.KeyRelease':
			self.lasttime=time.time()
			self.keyPressed2=False

		# enter and leave a widget - editor widgets
		if z == 'PySide.QtCore.QEvent.Type.Enter' or z == 'PySide.QtCore.QEvent.Type.Leave':
			pass

		# deactive keys in editors context
		if z == 'PySide.QtCore.QEvent.Type.Enter' and \
			(o.__class__ == QtGui.QPlainTextEdit or o.__class__ == QtGui.QTextEdit):
			self.editmode=True
		elif z == 'PySide.QtCore.QEvent.Type.Leave' and \
			(o.__class__ == QtGui.QPlainTextEdit or o.__class__ == QtGui.QTextEdit):
			self.editmode=False

		# mouse movement only leaves and enters
		if z == 'PySide.QtCore.QEvent.Type.HoverMove' :
			pass

		return QtGui.QWidget.eventFilter(self, o, e)

##\endcond

## draw a curve on a face and create the two subfaces defined by the curve

def drawcurve(wire,face):
	'''draw a curve on a face and create the two subfaces defined by the curve'''

	print "drawcurve"

	w=wire.Shape
	t=face

	pts=[p.Point for p in w.Vertexes]
	sf=t.Surface

	bs=sf
	su=bs.UPeriod()
	sv=bs.VPeriod()

	print "hacks etze uv, sv auf 1"
	su=face.ParameterRange[1]
	sv=face.ParameterRange[3]

#	print "debug mapp"
#	print "su ",su
#	print "sv ",sv
#	print "param range ", face.ParameterRange

	if su>1000: su=face.ParameterRange[1]
	if sv>1000: sv=face.ParameterRange[3]

	print "A"
	pts2da=[sf.parameter(p) for p in pts[1:]]
	print "B"
	pts2d=[FreeCAD.Base.Vector2d(p[0],p[1]) for p in pts2da]

	bs2d = Part.Geom2d.BSplineCurve2d()
	bs2d.setPeriodic()
	print "pts2d ..."
	print pts2d
	bs2d.interpolate(pts2d)
	bs2d.setPeriodic()

	e1 = bs2d.toShape(t)

	sp=App.ActiveDocument.getObject(wire.Label+"_Spline")
	if sp==None:
		sp=App.ActiveDocument.addObject("Part::Spline",wire.Label+"_Spline")
	sp.Shape=e1
	sp.ViewObject.LineColor=wire.ViewObject.LineColor


	edges=e1.Edges
	ee=edges[0]
	splita=[(ee,face)]
	r=Part.makeSplitShape(face, splita)

	ee.reverse()
	splitb=[(ee,face)]
	r2=Part.makeSplitShape(face, splitb)
	
	if hasattr(wire,"drawFace"):

			sp=App.ActiveDocument.getObject(wire.Label+"_SplineFaceA")
			if sp==None:
				sp=App.ActiveDocument.addObject("Part::Spline",wire.Label+"_SplineFaceA")

			if wire.reverseFace: sp.Shape=r2[0][0]
			else: sp.Shape=r[0][0]

			sp.ViewObject.ShapeColor=(random.random(),random.random(),random.random())
			sp.ViewObject.LineColor=sp.ViewObject.ShapeColor

			wire.ViewObject.LineColor=sp.ViewObject.ShapeColor
			wire.ViewObject.ShapeColor=sp.ViewObject.ShapeColor
			print "HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH"

## 	new wire for next drawing

def createnewwire(widget):
	'''new wire for next drawing'''

	ef=widget.ef

	w=App.ActiveDocument.addObject("Part::Feature","A Drawing on " + ef.objname + ": "+ ef.subelement +"#")
	w.Shape=Part.Shape()
	wam=App.ActiveDocument.addObject("Part::Feature","YY Drawing on " + ef.objname + ": "+ ef.subelement +"#")
	wam.Shape=Part.Shape()

	if 10:
		c=PySide.QtGui.QColorDialog.getColor(QtGui.QColor(random.randint(10,255),random.randint(10,255),random.randint(10,255)))
		w.ViewObject.LineColor=(1.0/255*c.red(),1.0/255*c.green(),1.0/255*c.blue())
		w.ViewObject.PointColor=(1.0/255*c.red(),1.0/255*c.green(),1.0/255*c.blue())
	else:
		w.ViewObject.LineColor=(random.random(),random.random(),random.random())

	ef.wire=w
	ef.wirem=wam
	ef.pts=[]



## dialog fpr facedrwaing options

class MyWidget(QtGui.QWidget):
	'''dialog for facedrawing '''

	def commit(self):
		'''stop the dialog and server'''
		stop()

	def apply(self):
		'''draw the curve and stop'''
		try: drawcurve(self.ef.wire,self.ef.subobj)
		except: sayexc2()
		stop()

	def applyandnew(self):
		'''draw the curve and start a new curve'''
		try: drawcurve(self.ef.wire,self.ef.subobj)
		except: sayexc2()
		createnewwire(self)

	def update(self):
		''' dummy method'''
		ef=self.ef
		print ("val,x,y,k",ef.mouseWheel,ef.posx,ef.posy,ef.key)
		return 

	def ef_action(self,*args):
		''' dummy method'''
		return


def dialog(source=None):
	''' create dialog widget'''

	w=MyWidget()
	w.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

	w.source=source
	w.imode=-1
	w.ef="no eventfilter defined"

#	mode=QtGui.QComboBox()
#	mode.addItem("move pole") #0
#	mode.addItem("move pole and neighbors") #1
#	mode.addItem("sharpen/smooth edge") #2
#	mode.addItem("colinear neighbors") #3
#	mode.addItem("rotate neighbors") #4
#
	w.mode='n'
#
	editorkey=FreeCAD.ParamGet('User parameter:Plugins/nurbs').GetString("editorKey","h")
#	lab=QtGui.QLabel("Direction: " + editorkey)
	w.key=editorkey
#	w.modelab=lab

	btn=QtGui.QPushButton("Apply and close")
	btn.clicked.connect(w.apply)

	cobtn=QtGui.QPushButton("Apply and new")
	cobtn.clicked.connect(w.applyandnew)

	cbtn=QtGui.QPushButton("Stop Dialog (preserve Aux)")
	cbtn.clicked.connect(stop)

#	poll=QtGui.QLabel("Selected  Pole:")

#	dial=QtGui.QDial() 
#	dial.setMaximum(10)
#	dial.setNotchesVisible(True)
#	dial.setValue(FreeCAD.ParamGet('User parameter:Plugins/nurbs').GetInt("Cursor",0))
#	dial.valueChanged.connect(w.setcursor2)
#	w.dial=dial


	box = QtGui.QVBoxLayout()
	w.setLayout(box)
	
	for ww in [btn,cobtn] :
		box.addWidget(ww)

	return w

## create the u-ribs and v-meridians for a surface

def createRibCage(bs,rc=100):
	'''create the u-ribs and v-meridians for a surface
	bs is a Bspline surface
	rc count of curves
	'''

	ribs=[]
	for i in range(rc+1):
		f=bs.uIso(1.0/rc*i)
		ribs.append(f.toShape())

	comp=Part.Compound(ribs)
	RibCage=App.activeDocument().addObject('Part::Feature','Ribs')
	RibCage.Shape=comp
	RibCage.ViewObject.LineWidth=1
	RibCage.ViewObject.Visibility=False

	mers=[]
	for i in range(rc+1):
		f=bs.vIso(1.0/rc*i)
		mers.append(f.toShape())
	comp=Part.Compound(mers)
	Meridians=App.activeDocument().addObject('Part::Feature','Meridians')
	Meridians.Shape=comp
	Meridians.ViewObject.LineWidth=1
	Meridians.ViewObject.Visibility=False
	return (RibCage,Meridians)


## create the inventor string for the colored wire

def genbuffer(pts,colors=None):
	'''create the inventor string for the colored wire
	pts - list of points
	colors - list of color indexes
	'''

	colix=""
	pix=""
	cordix=""
	for i,p in enumerate(pts):
		if i>0:
			if colors==None:colix += " "+str(random.randint(0,7))
			else:
				colix += " "+str(colors[i])
		pix += str(p.x)+" "+str(p.y) +" " +str(p.z)+"\n"
		if i>0:cordix +=  str(i-1)+" "+str(i)+" -1\n" 

	buff ='''#Inventor V2.1 ascii
	Separator {
		Transform {
			translation 0 0 0
			rotation 0 0 1  0
			scaleFactor 1 1 1
			center 0 0 0
		}
		Separator {
			VRMLGroup {
				children 
				VRMLShape {
					geometry 
						VRMLIndexedLineSet {
							coord 
								VRMLCoordinate {
									point 
	'''

	buff += " [" + pix + "]}\n"

	buff +='''
						color 
							VRMLColor {
								color [ 0 0 0, 1 0 0, 0 1 0,
										0 0 1, 1 1 0, 0 1 1, 1 0 1 , 1 1 1,
									]
							  }
						colorPerVertex FALSE
	'''

	buff += "colorIndex [" + colix + "]\n"
	buff += "coordIndex [" + cordix + "]\n"
	buff += "}}}}}"

	return buff


## create a vrml indexed color path as an inventor object

def drawColorpath(pts,colors,colorB=None,name='ColorPath'):
	'''create a vrml indexed color path as an inventor object
	pts is the list of points
	colors is the list of color indexes
	'''

	iv=App.ActiveDocument.getObject(name)
	if iv==None:iv=App.ActiveDocument.addObject("App::InventorObject",name)
	iv.Buffer=genbuffer(pts,colors)

## create and initialize the event filter

def start():
	'''create and initialize the event filter'''

	ef=EventFilter()
	ef.mouseWheel=0
	try:
			sel=Gui.Selection.getSelection()
			fob=sel[0]
			s=Gui.Selection.getSelectionEx()
			print s,s[0].SubObjects

			if len(s[0].SubObjects)>0:
				ef.subobj=s[0].SubObjects[0]
				ef.objname=s[0].Object.Name
				ef.subelement=s[0].SubElementNames[0]
			else:
				ef.subobj=fob.Shape.Face1
				ef.objname=fob.Name
				ef.subelement="Face1"

			if ef.subobj.Surface.__class__.__name__ == 'BSplineSurface':
				ef.rc=createRibCage(ef.subobj.Surface)

			ef.stack=[fob.ViewObject.Visibility,fob.ViewObject.Transparency,fob.ViewObject.Selectable]
			ef.fob=fob

			fob.ViewObject.Visibility=True
			fob.ViewObject.Transparency=70
			fob.ViewObject.Selectable=False

			Gui.Selection.clearSelection()

	except:
		sayexc2("no surface selected","Select first a face you want to draw on it")
		return

	FreeCAD.eventfilter=ef

	mw=QtGui.qApp
	mw.installEventFilter(ef)
	ef.keyPressed2=False

	# the result wire
	w=App.ActiveDocument.addObject("Part::Feature","Drawing on " + ef.objname + ": "+ ef.subelement)
	w.Shape=Part.Shape()
	w.ViewObject.Visibility=False
	w.ViewObject.LineColor=(1.0,0.0,0.0)
	w.ViewObject.LineWidth=10

	# the helper wire
	wam=App.ActiveDocument.addObject("Part::Feature","M_Drawing on " + ef.objname + ": "+ ef.subelement)
	wam.Shape=Part.Shape()
	wam.ViewObject.Visibility=False
	wam.ViewObject.LineColor=(1.0,0.0,1.0)
	wam.ViewObject.LineWidth=10

	ef.wire=w
	ef.wirem=wam

	ef.dialog=dialog()
	ef.dialog.ef=ef
	ef.dialog.show()

## create the 2D or 3D grid for the first face of a selected object

def createGrid(name="MyGrid"):
	'''create the 2D or 3D grid for the first face of a selected object'''

	sel=Gui.Selection.getSelection()
	fob=sel[0]

	b=FreeCAD.activeDocument().addObject("Part::FeaturePython",name)

	name=b.Name
	nurbswb.isodraw.Drawgrid(b)
	b.faceObject=fob

	b.ViewObject.Transparency=60
	App.activeDocument().recompute()

	b2=FreeCAD.activeDocument().addObject("Part::FeaturePython",name+"_2_")
	b2.Label=name+"_3D_"
	nurbswb.isodraw.Draw3Dgrid(b2)
	b2.drawgrid=b

## create a map control for the first face of the selected object

def createMap():
	''' create a mpa control for the first face of the selected object '''

	# last selection == face
	# other sels: wires to project

	s0=Gui.Selection.getSelection()
	face=s0[-1]

	moa=nurbswb.isodraw.createMap()
	moa.face=face


## stop the facecdraw eventserver

def stop():
	''' stop eventserver'''

	mw=QtGui.qApp
	ef=FreeCAD.eventfilter
	mw.removeEventFilter(ef)
	ef.keyPressed2=False

	ef.dialog.hide()

	try:
		App.ActiveDocument.removeObject(ef.rc[0].Name)
		App.ActiveDocument.removeObject(ef.rc[1].Name) 
	except:
		pass

	fob=ef.fob
	[fob.ViewObject.Visibility,fob.ViewObject.Transparency,fob.ViewObject.Selectable]=ef.stack

	App.ActiveDocument.removeObject(ef.wirem.Name)



## start the facedraw eventserver

def run():
	'''start the facedraw dialog and eventmanager'''

	try: stop()
	except: pass
	start()

