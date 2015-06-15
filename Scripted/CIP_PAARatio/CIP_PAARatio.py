# -*- coding: utf-8 -*-
import os
import unittest
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

# Add the CIP common library to the path if it has not been loaded yet
try:
    from CIP.logic import SlicerUtil
except Exception as ex:
    import inspect
    path = os.path.dirname(inspect.getfile(inspect.currentframe()))
    if os.path.exists(os.path.normpath(path + '/../CIP_Common')):
            path = os.path.normpath(path + '/../CIP_Common')        # We assume that CIP_Common is a sibling folder of the one that contains this module
    elif os.path.exists(os.path.normpath(path + '/CIP')):
            path = os.path.normpath(path + '/CIP')        # We assume that CIP is a subfolder (Slicer behaviour)
    sys.path.append(path)
    from CIP.logic import SlicerUtil
print("CIP was added to the python path manually in CIP_PAARatio")

from CIP.logic import Util

#
# CIP_PAARatio
#
class CIP_PAARatio(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "PAA Ratio"
        self.parent.categories = SlicerUtil.CIP_ModulesCategory
        self.parent.dependencies = [SlicerUtil.CIP_ModuleName]
        self.parent.contributors = ["Jorge Onieva (jonieva@bwh.harvard.edu)", "Applied Chest Imaging Laboratory", "Brigham and Women's Hospital"]
        self.parent.helpText = """Calculate the ratio between pulmonary arterial and aorta. This biomarker has been proved
                                to predict acute exacerbations of COPD (Wells, J. M., Washko, G. R., Han, M. K., Abbas,
                                N., Nath, H., Mamary, a. J., Dransfield, M. T. (2012). Pulmonary Arterial Enlargement and Acute Exacerbations
                                of COPD. New England Journal of Medicine, 367(10), 913-921).
                                For more information refer to:
                                http://www.nejm.org/doi/full/10.1056/NEJMoa1203830"""
        self.parent.acknowledgementText = SlicerUtil.ACIL_AcknowledgementText

#
# CIP_PAARatioWidget
#

class CIP_PAARatioWidget(ScriptedLoadableModuleWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """



    def setup(self):
        """This is called one time when the module GUI is initialized
        """
        ScriptedLoadableModuleWidget.setup(self)

        # Create objects that can be used anywhere in the module. Example: in most cases there should be just one
        # object of the logic class
        self.logic = CIP_PAARatioLogic()

        #
        # Create all the widgets. Example Area
        mainAreaCollapsibleButton = ctk.ctkCollapsibleButton()
        mainAreaCollapsibleButton.text = "Parameters"
        self.layout.addWidget(mainAreaCollapsibleButton)
        # Layout within the dummy collapsible button. See http://doc.qt.io/qt-4.8/layout.html for more info about layouts
        self.mainAreaLayout = qt.QFormLayout(mainAreaCollapsibleButton)

        self.volumeSelector = slicer.qMRMLNodeComboBox()
        self.volumeSelector.nodeTypes = ( "vtkMRMLScalarVolumeNode", "" )
        # DEPRECATED. Now there is a new vtkMRMLLabelMapNode
        #self.volumeSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", "0" )  # No labelmaps

        self.volumeSelector.selectNodeUponCreation = True
        self.volumeSelector.autoFillBackground = True
        self.volumeSelector.addEnabled = True
        self.volumeSelector.noneEnabled = False
        self.volumeSelector.removeEnabled = False
        self.volumeSelector.showHidden = False
        self.volumeSelector.showChildNodeTypes = False
        self.volumeSelector.setMRMLScene( slicer.mrmlScene )
        # self.volumeSelector.setToolTip( "Pick the volume" )
        self.mainAreaLayout.addWidget( self.volumeSelector )

        # Selector
        label = qt.QLabel("Select the structure")
        self.mainAreaLayout.addWidget(label)

        self.structuresCheckboxGroup=qt.QButtonGroup()
        btn = qt.QRadioButton("None")
        btn.checked = True
        self.structuresCheckboxGroup.addButton(btn)
        self.mainAreaLayout.addWidget(btn)

        btn = qt.QRadioButton("Aorta")
        self.structuresCheckboxGroup.addButton(btn)
        self.mainAreaLayout.addWidget(btn)

        btn = qt.QRadioButton("Pulmonary Arterial")
        self.structuresCheckboxGroup.addButton(btn)
        self.mainAreaLayout.addWidget(btn)

        btn = qt.QRadioButton("Both")
        self.structuresCheckboxGroup.addButton(btn)
        self.mainAreaLayout.addWidget(btn)


        self.placeDefaultRulersButton = ctk.ctkPushButton()
        self.placeDefaultRulersButton.text = "Place default rulers"
        self.placeDefaultRulersButton.toolTip = "This is the button tooltip"
        self.placeDefaultRulersButton.setIcon(qt.QIcon("{0}/Reload.png".format(Util.ICON_DIR)))
        self.placeDefaultRulersButton.setIconSize(qt.QSize(20,20))
        #self.placeRulerButton.setStyleSheet("font-weight:bold; font-size:12px" )
        self.placeDefaultRulersButton.setFixedWidth(200)
        self.mainAreaLayout.addWidget(self.placeDefaultRulersButton)

        self.placeRulersButton = ctk.ctkPushButton()
        self.placeRulersButton.text = "Place rulers"
        self.mainAreaLayout.addWidget(self.placeRulersButton)

        self.moveUpButton = ctk.ctkPushButton()
        self.moveUpButton.text = "Up"
        self.mainAreaLayout.addWidget(self.moveUpButton)

        self.moveDownButton = ctk.ctkPushButton()
        self.moveDownButton.text = "Down"
        self.mainAreaLayout.addWidget(self.moveDownButton)

        self.aortaTextBox = qt.QLineEdit()
        self.aortaTextBox.setReadOnly(True)
        self.mainAreaLayout.addRow("Aorta (mm):  ", self.aortaTextBox)

        self.paTextBox = qt.QLineEdit()
        self.paTextBox.setReadOnly(True)
        self.mainAreaLayout.addRow("PA (mm):  ", self.paTextBox)

        self.ratioTextBox = qt.QLineEdit()
        self.ratioTextBox.setReadOnly(True)
        self.mainAreaLayout.addRow("Ratio:  ", self.ratioTextBox)

        # Connections
        self.placeDefaultRulersButton.connect('clicked()', self.onPlaceDefaultRulers)
        self.placeRulersButton.connect('clicked()', self.onPlaceRuler)
        self.moveUpButton.connect('clicked()', self.onMoveUpRuler)
        self.moveDownButton.connect('clicked()', self.onMoveDownRuler)


    def enter(self):
        """This is invoked every time that we select this module as the active module in Slicer (not only the first time)"""
        pass

    def exit(self):
        """This is invoked every time that we switch to another module (not only when Slicer is closed)."""
        pass

    def cleanup(self):
        """This is invoked as a destructor of the GUI when the module is no longer going to be used"""
        pass


    def placeDefaultRulers(self, volumeId):
        """
        :param volumeId: Set the Aorta and PA rulers to a default estimated position
        :return:
        """
        if volumeId == '':
            self.showUnselectedVolumeWarningMessage()
            return

        rulerNodeAorta, isNewAorta, rulerNodePA, isNewPA = self.logic.createDefaultRulers(volumeId)

        if isNewAorta:
            rulerNodeAorta.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onRulerUpdated)
        if isNewPA:
            rulerNodePA.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onRulerUpdated)

        # Get the coordinates of one of the rulers and jump to that slice
        coords = [0, 0, 0, 0]
        # Get current RAS coords
        rulerNodeAorta.GetPositionWorldCoordinates1(coords)
        # Set the display in the right slice
        self.moveRedWindowToSlice(coords[2])

        self.refreshTextboxes()

    def placeRuler(self):
        """ Place one or the two rulers in the current visible slice in Red node
        """
        volumeId = self.volumeSelector.currentNodeId
        if volumeId == '':
            self.showUnselectedVolumeWarningMessage()
            return

        selectedStructure = self.getCurrentSelectedStructure()
        if selectedStructure == self.logic.NONE:
            qt.QMessageBox.warning(slicer.util.mainWindow(), 'Review structure',
                'Please select Aorta or Pulmonary Arterial to place the right ruler')
            return

        # Get the current slice
        currentSlice = self.getCurrentRedWindowSlice()

        rulerNode, newNode = self.logic.placeRulerInSlice(volumeId, selectedStructure, currentSlice)

        if newNode:
             rulerNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onRulerUpdated)
             self.refreshTextboxes()

        # rulerNode = self.logic.getRulerNodeForVolumeAndStructure(volumeId, selectedStructure)
        # # Get the current slice
        # layoutManager = slicer.app.layoutManager()
        # redWidget = layoutManager.sliceWidget('Red')
        # redNodeSliceNode = redWidget.sliceLogic().GetSliceNode()
        # rasSliceOffset = redNodeSliceNode.GetSliceOffset()
        #
        #  # Create the node in the current slice
        # # TODO: conversion RAS -> IJK?
        # defaultXY1 = [0, 50, rasSliceOffset]
        # defaultXY2 = [0, 100, rasSliceOffset]
        #
        # coords1 = [defaultXY1[0], defaultXY1[1], rasSliceOffset]
        # coords2 = [defaultXY2[0], defaultXY2[1], rasSliceOffset]
        # rulerNode.SetPosition1(coords1)
        # rulerNode.SetPosition2(coords2)

    def getCurrentSelectedStructure(self):
        """ Get the current selected structure id
        :return: self.logic.AORTA or self.logic.PA
        """
        selectedStructureText = self.structuresCheckboxGroup.checkedButton().text
        if selectedStructureText == "Aorta": return self.logic.AORTA
        elif selectedStructureText == "Pulmonary Arterial": return  self.logic.PA
        elif selectedStructureText == "Both": return self.logic.BOTH
        return self.logic.NONE

    def stepSlice(self, offset):
        """ Move the selected structure one slice up or down
        :param offset: +1 or -1
        :return:
        """
        volumeId = self.volumeSelector.currentNodeId

        if volumeId == '':
            self.showUnselectedVolumeWarningMessage()
            return

        selectedStructure = self.getCurrentSelectedStructure()
        if selectedStructure == self.logic.NONE:
            self.showUnselectedStructureWarningMessage()
            return

        if selectedStructure == self.logic.BOTH:
            # Move both rulers
            self.logic.moveSliceOffset(volumeId, self.logic.AORTA, offset)
            newSlice = self.logic.stepSlice(volumeId, self.logic.PA, offset)
        else:
            newSlice = self.logic.stepSlice(volumeId, selectedStructure, offset)

        self.moveRedWindowToSlice(newSlice)

    def getCurrentRedWindowSlice(self):
        """ Get the current slice (in RAS) of the Red window
        :return:
        """
        redNodeSliceNode = slicer.app.layoutManager().sliceWidget('Red').sliceLogic().GetSliceNode()
        return redNodeSliceNode.GetSliceOffset()

    def moveRedWindowToSlice(self, newSlice):
        """ Moves the red display to the specified RAS slice
        :param newSlice: slice to jump (RAS format)
        :return:
        """
        redNodeSliceNode = slicer.app.layoutManager().sliceWidget('Red').sliceLogic().GetSliceNode()
        redNodeSliceNode.JumpSlice(0,0,newSlice)

    def refreshTextboxes(self):
        """ Update the information of the textboxes that give information about the measurements
        """
        rulerAorta, newAorta = self.logic.getRulerNodeForVolumeAndStructure(self.volumeSelector.currentNodeId, self.logic.AORTA)
        rulerPA, newPA = self.logic.getRulerNodeForVolumeAndStructure(self.volumeSelector.currentNodeId, self.logic.PA)
        if not newAorta:
            self.aortaTextBox.setText(str(rulerAorta.GetDistanceMeasurement()))
        if not newPA:
            self.paTextBox.setText(str(rulerPA.GetDistanceMeasurement()))
        try:
            self.ratioTextBox.setText(str(rulerPA.GetDistanceMeasurement() / rulerAorta.GetDistanceMeasurement()))
        except Exception as exc:
            print(exc.message)

    def showUnselectedVolumeWarningMessage(self):
        qt.QMessageBox.warning(slicer.util.mainWindow(), 'Select a volume',
                'Please select a volume')

    def showUnselectedStructureWarningMessage(self):
        qt.QMessageBox.warning(slicer.util.mainWindow(), 'Review structure',
                'Please select Aorta, Pulmonary Arterial or Both to place the right ruler/s')

    #########
    # EVENTS
    def onStructureClicked(self, button):
        fiducialsNode = self.getFiducialsNode(self.volumeSelector.currentNodeId)
        if fiducialsNode is not None:
            self.__addRuler__(button.text, self.volumeSelector.currentNodeId)

            markupsLogic = slicer.modules.markups.logic()
            markupsLogic.SetActiveListID(fiducialsNode)

            applicationLogic = slicer.app.applicationLogic()
            selectionNode = applicationLogic.GetSelectionNode()

            selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLAnnotationRulerNode")
            interactionNode = applicationLogic.GetInteractionNode()
            interactionNode.SwitchToSinglePlaceMode()

    def onPlaceDefaultRulers(self):
        self.placeDefaultRulers(self.volumeSelector.currentNodeId)

    def onRulerUpdated(self, node, event):
        self.refreshTextboxes()

    def onPlaceRuler(self):
        self.placeRuler()

    def onMoveUpRuler(self):
        self.stepSlice(1)

    def onMoveDownRuler(self):
        self.stepSlice(-1)
#
# CIP_PAARatioLogic
#
class CIP_PAARatioLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.    The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    NONE = 0
    AORTA = 1
    PA = 2
    BOTH = 3
    SLICEFACTOR = 0.6

    # Default XY coordinates for Aorta and PA (the Z will be stimated depending on the number of slices)
    defaultAorta1 = [220, 170, 0]
    defaultAorta2 = [275, 175, 0]
    defaultPA1 = [280, 175, 0]
    defaultPA2 = [320, 190, 0]

    def __init__(self):
        pass

    def getRootAnnotationsNode(self):
        """ Get the root annotations node global to the scene, creating it if necessary
        :return: "All Annotations" vtkMRMLAnnotationHierarchyNode
        """
        rootHierarchyNode = slicer.util.getNode('All Annotations')
        if rootHierarchyNode is None:
            # Create root annotations node
            rootHierarchyNode = slicer.modules.annotations.logic().GetActiveHierarchyNode()
            logging.debug("Root annotations node created")
        return rootHierarchyNode

    def getRulersListNode(self, volumeId):
        """ Get the rulers node for this volume, creating it if it doesn't exist yet
        :param volumeId:
        :return: "volumeId_paaRulersNode" vtkMRMLAnnotationHierarchyNode
        """
        # Search for the current volume hierarchy node (each volume has its own hierarchy)
        nodeName = volumeId + '_paaRulersNode'
        rulersNode = slicer.util.getNode(nodeName)

        if rulersNode is None:
            # Create the node
            annotationsLogic = slicer.modules.annotations.logic()
            rootHierarchyNode = self.getRootAnnotationsNode()
            annotationsLogic.SetActiveHierarchyNodeID(rootHierarchyNode.GetID())
            annotationsLogic.AddHierarchy()
            n = rootHierarchyNode.GetNumberOfChildrenNodes()
            rulersNode = rootHierarchyNode.GetNthChildNode(n-1)
            # Rename the node
            rulersNode.SetName(nodeName)
            logging.debug("Created node " + nodeName + " (general rulers node for this volume")
        # Return the node
        return rulersNode

    def getRulerNodeForVolumeAndStructure(self, volumeId, structureId):
        """ Search for the right ruler node to be created based on the volume and the selected
        structure (Aorta or PA).
        It also creates the necessary node hierarchy if it doesn't exist.
        :param volumeId:
        :param structureId: Aorta (1), PA (2)
        :return: node and a boolean indicating if the node has been created now
        """
        isNewNode = False
        if structureId == 0: # none
            return None, isNewNode
        if structureId == self.AORTA:     # Aorta
             #nodeName = volumeId + '_paaRulers_aorta'
            nodeName = "A"
        elif structureId == self.PA:   # 'Pulmonary Arterial':
        #     nodeName = volumeId + '_paaRulers_pa'
            nodeName = "PA"
        # Get the node that contains all the rulers
        rulersListNode = self.getRulersListNode(volumeId)
        # Search for the node
        node = None
        for i in range(rulersListNode.GetNumberOfChildrenNodes()):
            nodeWrapper = rulersListNode.GetNthChildNode(i)
            # nodeWrapper is also a HierarchyNode. We need to look for its only child that will be the rulerNode
            col = vtk.vtkCollection()
            nodeWrapper.GetChildrenDisplayableNodes(col)
            rulerNode = col.GetItemAsObject(0)

            if rulerNode.GetName() == nodeName:
                node = rulerNode
                break

        if node is None:
            # Create the node
            # Set the active node, so that the new ruler is a child node
            annotationsLogic = slicer.modules.annotations.logic()
            annotationsLogic.SetActiveHierarchyNodeID(rulersListNode.GetID())
            node = slicer.mrmlScene.CreateNodeByClass('vtkMRMLAnnotationRulerNode')
            node.SetName(nodeName)
            slicer.mrmlScene.AddNode(node)
            isNewNode = True
            logging.debug("Created node " + nodeName + " for volume " + volumeId)

        return node, isNewNode

    def createDefaultRulers(self, volumeId):
        """ Set the Aorta and PA rulers to their default position.
        The X and Y will be configured in "defaultAorta1, defaultAorta2, defaultPA1, defaultPA2" properties
        The Z will be estimated based on the number of slices of the volume
        :param volumeId:
        :return: a tuple of 4 vales. For each node, return the node and a boolean indicating if the node was
        created now
        """
        aorta1, aorta2, pa1, pa2 = self.getDefaultCoords(volumeId)

        rulerNodeAorta, newNodeAorta = self.getRulerNodeForVolumeAndStructure(volumeId, self.AORTA)
        rulerNodeAorta.SetPositionWorldCoordinates1(aorta1)
        rulerNodeAorta.SetPositionWorldCoordinates2(aorta2)

        rulerNodePA, newNodePA = self.getRulerNodeForVolumeAndStructure(volumeId, self.PA)
        rulerNodePA.SetPositionWorldCoordinates1(pa1)
        rulerNodePA.SetPositionWorldCoordinates2(pa2)

        return rulerNodeAorta, newNodeAorta, rulerNodePA, newNodePA

    def stepSlice(self, volumeId, structureId, sliceStep):
        """ Move the selected ruler up or down one slice.
        :param volumeId:
        :param structureId:
        :param sliceStep: +1 or -1
        :return: new slice in RAS format
        """
        # Calculate the RAS coords of the slice where we should jump to
        rulerNode, newNode = self.getRulerNodeForVolumeAndStructure(volumeId, structureId)
        if newNode:
            return False

        coords = [0, 0, 0, 0]
        # Get current RAS coords
        rulerNode.GetPositionWorldCoordinates1(coords)

        # Get the transformation matrixes
        rastoijk=vtk.vtkMatrix4x4()
        ijktoras=vtk.vtkMatrix4x4()
        scalarVolumeNode = slicer.mrmlScene.GetNodeByID(volumeId)
        scalarVolumeNode.GetRASToIJKMatrix(rastoijk)
        scalarVolumeNode.GetIJKToRASMatrix(ijktoras)

        # Get the current slice (Z). It will be the same in both positions
        ijkCoords = list(rastoijk.MultiplyPoint(coords))

        # Add/substract the offset to Z
        ijkCoords[2] += sliceStep
        # Convert back to RAS, just replacing the Z
        newSlice = ijktoras.MultiplyPoint(ijkCoords)[2]

        self._placeRulerInSlice_(rulerNode, structureId, newSlice)

        return newSlice

    def placeRulerInSlice(self, volumeId, structureId, newSlice):
        """ Move the ruler to the specified slice (in RAS format)
        :param volumeId:
        :param structureId:
        :param newSlice: slice in RAS format
        :return: tuple with ruler node and a boolean indicating if the node was just created
        """
        # Get the correct ruler
        rulerNode, newNode = self.getRulerNodeForVolumeAndStructure(volumeId, structureId)

        # Move the ruler
        self._placeRulerInSlice_(rulerNode, structureId, newSlice)

        return rulerNode, newNode

    def _placeRulerInSlice_(self, rulerNode, structureId, newSlice):
        """ Move the ruler to the specified slice (in RAS format)
        :param rulerNode: node of type vtkMRMLAnnotationRulerNode
        :param newSlice: slice in RAS format
        :return: True if the operation was succesful
        """
        coords1 = [0, 0, 0, 0]
        coords2 = [0, 0, 0, 0]
        # Get RAS coords of the ruler node
        rulerNode.GetPositionWorldCoordinates1(coords1)
        rulerNode.GetPositionWorldCoordinates2(coords2)

        # Set the slice of the coordinate
        coords1[2] = coords2[2] = newSlice

        if coords1[0] == 0 and coords1[1] == 0:
            # New node, get default coordinates depending on the structure
            if structureId == self.AORTA:
                coords1[0] = self.defaultAorta1[0]
                coords1[1] = self.defaultAorta1[1]
                coords2[0] = self.defaultAorta2[0]
                coords2[1] = self.defaultAorta2[1]
            elif structureId == self.PA:
                coords1[0] = self.defaultPA1[0]
                coords1[1] = self.defaultPA1[1]
                coords2[0] = self.defaultPA2[0]
                coords2[1] = self.defaultPA2[1]


        rulerNode.SetPositionWorldCoordinates1(coords1)
        rulerNode.SetPositionWorldCoordinates2(coords2)

    def getDefaultCoords(self, volumeId):
        """ Get the default coords for aorta and PA in this volume (RAS format)
        :param volumeId:
        :return: (aorta1, aorta2, pa1, pa2). All of them lists of 3 positions in RAS format
        """
        volume = slicer.mrmlScene.GetNodeByID(volumeId)
        rasBounds = [0,0,0,0,0,0]
        volume.GetRASBounds(rasBounds)
        # Get the slice (Z)
        ijk = self.RAStoIJK(volume, [0, 0, rasBounds[5]])
        slice = int(ijk[2] * self.SLICEFACTOR)       # Empiric stimation

        # Get the default coords, converting from IJK to RAS
        aorta1 = list(self.defaultAorta1)
        aorta1[2] = slice
        aorta1 = self.IJKtoRAS(volume, aorta1)
        aorta2 = list(self.defaultAorta2)
        aorta2[2] = slice
        aorta2 = self.IJKtoRAS(volume, aorta2)
        
        pa1 = list(self.defaultPA1)
        pa1[2] = slice
        pa1 = self.IJKtoRAS(volume, pa1)
        pa2 = list(self.defaultPA2)
        pa2[2] = slice
        pa2 = self.IJKtoRAS(volume, pa2)

        return aorta1, aorta2, pa1, pa2

    def RAStoIJK(self, volumeNode, rasCoords):
        """ Transform a list of RAS coords in IJK for a volume
        :return: list of IJK coordinates
        """
        rastoijk=vtk.vtkMatrix4x4()
        volumeNode.GetRASToIJKMatrix(rastoijk)
        rasCoords.append(1)
        return list(rastoijk.MultiplyPoint(rasCoords))

    def IJKtoRAS(self, volumeNode, ijkCoords):
        """ Transform a list of IJK coords in RAS for a volume
        :return: list of RAS coordinates
        """
        ijktoras=vtk.vtkMatrix4x4()
        volumeNode.GetIJKToRASMatrix(ijktoras)
        ijkCoords.append(1)
        return list(ijktoras.MultiplyPoint(ijkCoords))



class CIP_PAARatioTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_CIP_PAARatio_PrintMessage()

    def test_CIP_PAARatio_PrintMessage(self):
        self.delayDisplay("Starting the test")
        logic = CIP_PAARatioLogic()

        myMessage = "Print this test message in console"
        logging.info("Starting the test with this message: " + myMessage)
        expectedMessage = "I have printed this message: " + myMessage
        logging.info("The expected message would be: " + expectedMessage)
        responseMessage = logic.printMessage(myMessage)
        logging.info("The response message was: " + responseMessage)
        self.assertTrue(responseMessage == expectedMessage)
        self.delayDisplay('Test passed!')
