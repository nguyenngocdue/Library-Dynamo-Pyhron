import clr
import System
import math 
from System.Collections.Generic import *

clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *

clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *

clr.AddReference('RevitAPIUI')
from Autodesk.Revit.UI import*
from  Autodesk.Revit.UI.Selection import*

clr.AddReference("RevitNodes")
import Revit
clr.ImportExtensions(Revit.Elements)
clr.ImportExtensions(Revit.GeometryConversion)

clr.AddReference("RevitServices")
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument
view = doc.ActiveView
uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument


def lstFlattenL1(list): 
    result = []
    for i in list:
        result.append(i)
    return result
def lstFlattenL2(list):
    result = []
    for i in list:
        for j in i:
            result.append(j)
    return result
class SelectionFilter(ISelectionFilter):
	def __init__(self, ctgName1 , ctgName2):
		self.ctgName1 = ctgName1
		self.ctgName2 = ctgName2

	def AllowElement(self, element):
		if element.Category.Name == self.ctgName1 or element.Category.Name == self.ctgName2:
			return True
		else:
			return False
	def AllowReference(ref, xyZ):
		return False
		return False

def GetGeoElement(element): # Get geometry of element.
    geo = []
    opt = Options()
    opt.ComputeReferences = True
    opt.IncludeNonVisibleObjects = True
    opt.DetailLevel = ViewDetailLevel.Fine
    geoByElement = element.get_Geometry(opt)
    geo = [i for i in geoByElement]
    return geo


def GetSolidFromGeo(lstGeo): # Get Solid from Geo
    sol = []
    for i in lstGeo:
        if i.GetType()== Solid and i.Volume > 0:
            sol.append(i)
        elif i.GetType() == GeometryInstance:
            var = i.SymbolGeometry
            for j in var:
                if j.Volume > 0:
                    sol.append(j)
    return sol

def GetPlanarFormSolid(solids): # Get Planarface from solids
    plaf = []
    for i in solids:
        var = i.Faces
        for j in var:
            if j.Reference != None:
                plaf.append(j)
    return plaf

def Isparalel(p,q):
    return p.CrossProduct(q).IsZeroLength()

def FilterVerticalPlanar(lstPlface): # Get Vertical PlannarFaces 
    faV = []
    y = XYZ.BasisY
    for i in lstPlface:
        faNomal = i.FaceNormal
        check  = Isparalel(y,faNomal)
        if check == True:
            faV.append(i)
    return faV

def GetReferenceArray(lstPlanar):
    reArray = ReferenceArray()
    for i in lstPlanar:
        reArray.Append(i.Reference)
    return reArray

def RetrieveEdgesFace(lstPlanar): # Get Lines of PlanarFaces
    re = []
    var = lstPlanar.EdgeLoops
    for i in var:
        for j in i:
            re.append(j.AsCurve())
    return re
def GetLineMax(lstLine): # Get a min line of list line
    _length = []
    lineMax = []
    for i in lstLine:
        _length.append(i.Length)
    for j in lstLine:
        if j.Length == max(_length):
            lineMax.append(j)
    return lineMax
def RemoveFaceNone(lstplanars): # Get planarFaces Not Null Value
    pfaces = []
    for i in lstplanars:
        if i.Reference != None:
            pfaces.append(i)
    return pfaces
def GetFaceVertical(plannar): # Get Vertical PlannarFaces 
    re = []
    remove = RemoveFaceNone(plannar)
    for i in remove:
        var = i.FaceNormal
        rad = var.AngleTo(XYZ.BasisZ)
        if 30<(rad*180/3.14)<170:
            re.append(i)
    return re

def GetMaxface(plananrs):
    _Area = []
    _face = []
    for i in plananrs:
        _Area.append(i.Area)
    for j in plananrs:
        if j.Area > min(_Area)*2:
            _face.append(j)
            
    return _face

def GetLineMax(lstLine): # Get a min line of list line
    _length = []
    lineMax = []
    for i in lstLine:
        _length.append(i.Length)
    for j in lstLine:
        if j.Length == max(_length):
            lineMax.append(j)
    return lineMax

ele = SelectionFilter("NOT", "Structural Framing")
elSelectAll = uidoc.Selection.PickElementsByRectangle(ele,"Selects")
elSelect= [elSelectAll[0]]
eleFraming = elSelectAll

getGeoFraming = [GetGeoElement(i) for i in eleFraming]
OUT = getGeoFraming

getSolidFraming = [GetSolidFromGeo(i) for i in getGeoFraming]
OUT = getSolidFraming

getFaceFraming = lstFlattenL2([GetPlanarFormSolid(i) for i in getSolidFraming])
OUT = [i.ToProtoType()for i in  getFaceFraming]



getFaVerFraming = GetFaceVertical(getFaceFraming)
getFaceMax = GetMaxface(getFaVerFraming)
OUT = [i.ToProtoType()for i in  getFaceMax]
OUT = getFaceMax




bot_EdgesPlanarFraming = RetrieveEdgesFace(getFaceFraming[0])
OUT = [i.ToProtoType()for i in  bot_EdgesPlanarFraming]


getLineMax = GetLineMax(bot_EdgesPlanarFraming)[0]
OUT = getLineMax.ToProtoType()



##################################################
vtxPlane = XYZ.BasisZ
vtxSection = XYZ.BasisY

ptsLine1 = getLineMax.GetEndPoint(0)
ptsLine2 = getLineMax.GetEndPoint(1)

vtxFromLine = ptsLine1 - ptsLine2

pickPoint = uidoc.Selection.PickPoint("Select Point")
direct = vtxPlane.CrossProduct(vtxFromLine) 
line = Line.CreateBound(pickPoint,pickPoint+direct)
###################################################

reArrayVer_Framing = GetReferenceArray(getFaceMax)
OUT =  [i.ToProtoType()for i in  getFaceMax] , reArrayVer_Framing



TransactionManager.Instance.EnsureInTransaction(doc)

#dim1 = doc.Create.NewDimension(view, line, reArrayVer_Framing)

TransactionManager.Instance.TransactionTaskDone()


OUT = line.ToProtoType()
OUT = vtxPlane
