# -*- coding: utf-8 -*-
"""To handle input from keyboard, mouse and joystick (joysticks require pygame to be installed).
See demo_mouse.py and i{demo_joystick.py} for examples
"""
# Part of the PsychoPy library
# Copyright (C) 2011 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

# 01/2011 modified by Dave Britton to get mouse event timing 

import sys, time, copy
import psychopy.core, psychopy.misc, psychopy.visual
from psychopy import log
import string, numpy

#try to import pyglet & pygame and hope the user has at least one of them!
try:
    from pygame import mouse, locals, joystick, display
    import pygame.key
    import pygame.event as evt
    havePygame = True
except:
    havePygame = False
    
try:
    import pyglet.window
    havePyglet = True
except:
    havePyglet = False
if havePygame: usePygame=True#will become false later if win not initialised
else: usePygame=False   

if havePyglet:
    
    global _keyBuffer
    _keyBuffer = []
    global mouseButtons
    mouseButtons = [0,0,0]
    global mouseWheelRel
    mouseWheelRel = numpy.array([0.0,0.0])
    global mouseClick # list of 3 clocks that are reset on mouse button presses
    mouseClick = [psychopy.core.Clock(),psychopy.core.Clock(),psychopy.core.Clock()]
    global mouseTimes
    mouseTimes = [0.0,0.0,0.0] # container for time elapsed from last reset of mouseClick[n] for any button pressed
    global mouseMove # clock for tracking time of mouse movement, reset when mouse is moved
    mouseMove = psychopy.core.Clock() # reset on mouse motion
    #global eventThread
    #eventThread = _EventDispatchThread()
    #eventThread.start()

def _onPygletKey(symbol, modifiers): 
    """handler for on_key_press events from pyglet 
    Adds a key event to global _keyBuffer which can then be accessed as normal 
    using event.getKeys(), .waitKeys(), clearBuffer() etc... 
    Appends a tuple with (keyname, timepressed) into the _keyBuffer"""
    keyTime=psychopy.core.getTime() #capture when the key was pressed
    thisKey = pyglet.window.key.symbol_string(symbol).lower()#convert symbol into key string
    #convert pyglet symbols to pygame forms ( '_1'='1', 'NUM_1'='[1]')
    thisKey = (thisKey.lstrip('_').lstrip('NUM_'),keyTime) # modified to capture time of keypress so key=(keyname,keytime)
    _keyBuffer.append(thisKey)
    log.data("Keypress: %s" %thisKey[0])
    
def _onPygletMousePress(x,y, button, modifiers):
    global mouseButtons, mouseClick, mouseTimes
    if button == pyglet.window.mouse.LEFT:
        mouseButtons[0]=1
        mouseTimes[0]= psychopy.core.getTime()-mouseClick[0].timeAtLastReset
        label='Left'
    if button == pyglet.window.mouse.MIDDLE: 
        mouseButtons[1]=1
        mouseTimes[1]= psychopy.core.getTime()-mouseClick[1].timeAtLastReset
        label='Middle'
    if button == pyglet.window.mouse.RIGHT:
        mouseButtons[2]=1
        mouseTimes[2]= psychopy.core.getTime()-mouseClick[2].timeAtLastReset
        label='Right'
    log.data("Mouse: %s button down, pos=(%i,%i)" %(label, x,y))

def _onPygletMouseRelease(x,y, button, modifiers):
    global mouseButtons
    if button == pyglet.window.mouse.LEFT: 
        mouseButtons[0]=0
        label='Left'
    if button == pyglet.window.mouse.MIDDLE: 
        mouseButtons[1]=0
        label='Middle'
    if button == pyglet.window.mouse.RIGHT: 
        mouseButtons[2]=0
        label='Right'
    log.data("Mouse: %s button up, pos=(%i,%i)" %(label, x,y))

def _onPygletMouseWheel(x,y,scroll_x, scroll_y):
    global mouseWheelRel
    mouseWheelRel = mouseWheelRel+numpy.array([scroll_x, scroll_y])
    log.data("Mouse: wheel shift=(%i,%i), pos=(%i,%i)" %(scroll_x, scroll_y,x,y))

def _onPygletMouseMotion(x, y, dx, dy): # will this work? how are pyglet event handlers defined?
    global mouseMove
    # mouseMove is a core.Clock() that is reset when the mouse moves
    # default is None, but start and stopMoveClock() create and remove it, mouseMove.reset() resets it by hand
    if mouseMove: mouseMove.reset() 

def startMoveClock():
    global mouseMove
    mouseMove=psychopy.core.Clock()

def stopMoveClock():
    global mouseMove
    mouseMove=None

def resetMoveClock():
    global mouseMove
    if mouseMove: mouseMove.reset()
    else: startMoveClock()

def getKeys(keyList=None, timeStamped=False):
    """Returns a list of keys that were pressed.
        
    :Parameters:
        keyList : **None** or []
            Allows the user to specify a set of keys to check for.
            Only keypresses from this set of keys will be removed from the keyboard buffer. 
            If the keyList is None all keys will be checked and the key buffer will be cleared
            completely. NB, pygame doesn't return timestamps (they are always 0)
        timeStamped : **False** or True or `Clock`
            If True will return a list of 
            tuples instead of a list of keynames. Each tuple has (keyname, time). 
            If a `core.Clock` is given then the time will be relative to the `Clock`'s last reset
            
    :Author:
        - 2003 written by Jon Peirce
        - 2009 keyList functionality added by Gary Strangman
        - 2009 timeStamped code provided by Dave Britton
    """
    keys=[]


    if havePygame and display.get_init():#see if pygame has anything instead (if it exists)
        for evts in evt.get(locals.KEYDOWN):
            keys.append( (pygame.key.name(evts.key),0) )#pygame has no keytimes

    elif havePyglet:
        #for each (pyglet) window, dispatch its events before checking event buffer
        wins = pyglet.window.get_platform().get_default_display().get_windows()
        for win in wins: win.dispatch_events()#pump events on pyglet windows

        global _keyBuffer
        if len(_keyBuffer)>0:
            #then pyglet is running - just use this
            keys = _keyBuffer
    #        _keyBuffer = []  # DO /NOT/ CLEAR THE KEY BUFFER ENTIRELY
    
    if keyList==None:
        _keyBuffer = [] #clear buffer entirely
        targets=keys  # equivalent behavior to getKeys()
    else:
        nontargets = []
        targets = []
        # split keys into keepers and pass-thrus
        for key in keys:
            if key[0] in keyList:
                targets.append(key)
            else:
                nontargets.append(key)
        _keyBuffer = nontargets  # save these
        
    #now we have a list of tuples called targets
    #did the user want timestamped tuples or keynames?
    if timeStamped==False:
        keyNames = [k[0] for k in targets]
        return keyNames
    elif hasattr(timeStamped, 'timeAtLastReset'):
        relTuple = [(k[0],k[1]-timeStamped.timeAtLastReset) for k in targets]
        return relTuple
    elif timeStamped==True:
        return targets

def waitKeys(maxWait = None, keyList=None):
    """
    Halts everything (including drawing) while awaiting
    input from keyboard. Then returns *list* of keys pressed. Implicitly clears
    keyboard, so any preceding keypresses will be lost.
    
    Optional arguments specify maximum wait period and which keys to wait for. 
    
    Returns None if times out.
    """
    
    #NB pygame.event does have a wait() function that will
    #do this and maybe leave more cpu idle time?
    key=None
    clearEvents('keyboard')#so that we only take presses from here onwards.
    if maxWait!=None and keyList!=None:
        #check keylist AND timer
        timer = psychopy.core.Clock()
        while key==None and timer.getTime()<maxWait:     
            if havePyglet:       
                wins = pyglet.window.get_platform().get_default_display().get_windows()
                for win in wins: win.dispatch_events()#pump events on pyglet windows
            keys = getKeys()
            #check if we got a key in list
            if len(keys)>0 and (keys[0] in keyList): 
                key = keys[0]
            
    elif keyList!=None:
        #check the keyList each time there's a press
        while key==None:        
            if havePyglet:    
                wins = pyglet.window.get_platform().get_default_display().get_windows()
                for win in wins: win.dispatch_events()#pump events on pyglet windows
            keys = getKeys()
            #check if we got a key in list
            if len(keys)>0 and (keys[0] in keyList): 
                key = keys[0]
            
    elif maxWait!=None:
        #onyl wait for the maxWait 
        timer = psychopy.core.Clock()
        while key==None and timer.getTime()<maxWait:       
            if havePyglet:          
                wins = pyglet.window.get_platform().get_default_display().get_windows()
                for win in wins: win.dispatch_events()#pump events on pyglet windows
            keys = getKeys()
            #check if we got a key in list
            if len(keys)>0: 
                key = keys[0]
            
    else: #simply take the first key we get
        while key==None:      
            if havePyglet:           
                wins = pyglet.window.get_platform().get_default_display().get_windows()
                for win in wins: win.dispatch_events()#pump events on pyglet windows
            keys = getKeys()
            #check if we got a key in list
            if len(keys)>0: 
                key = keys[0]
        
    #after the wait period or received a valid keypress
    if key:
        log.data("Key pressed: %s" %key)
        return [key]#need to convert back to a list
    else:
        return None #no keypress in period

def xydist(p1=[0.0,0.0],p2=[0.0,0.0]):
    """Helper function returning the cartesian distance between p1 and p2
    """
    return numpy.sqrt(pow(p1[0]-p2[0],2)+pow(p1[1]-p2[1],2))

class Mouse:
    """Easy way to track what your mouse is doing.
    It needn't be a class, but since Joystick works better
    as a class this may as well be one too for consistency
    
    Create your `visual.Window` before creating a Mouse.
    
    :Parameters:
        visible : **True** or False
            makes the mouse invisbile if necessary
        newPos : **None** or [x,y]
            gives the mouse a particular starting position (pygame `Window` only)
        win : **None** or `Window`
            the window to which this mouse is attached (the first found if None provided)

    """
    def __init__(self,
                 visible=True,
                 newPos=None,
                 win=None):
        self.visible=visible
        self.lastPos = None
        self.prevPos = None # used for motion detection and timing
        self.win=win
        self.mouseClock=psychopy.core.Clock() # used for movement timing
        self.movedistance=0.0
        #if pygame isn't initialised then we must use pyglet
        if (havePygame and not pygame.display.get_init()):
            global usePygame
            usePygame=False
        
        if newPos is not None: self.setPos(newPos)
        
    def setPos(self,newPos=(0,0)):
        """Sets the current postiion of the mouse (pygame only), 
        in the same units as the :class:`~visual.Window` (0,0) is at centre
        
        :Parameters:
            newPos : (x,y) or [x,y]
                the new position on the screen

        """
        newPosPix = self._windowUnits2pix(numpy.array(newPos))
        if usePygame: 
            newPosPix[1] = self.win.size[1]/2-newPosPix[1]
            newPosPix[0] = self.win.size[0]/2+newPosPix[0]
            print newPosPix
            mouse.set_pos(newPosPix)
        else: print "pyglet does not support setting the mouse position yet"
        
    def getPos(self):
        """Returns the current postion of the mouse, 
        in the same units as the :class:`~visual.Window` (0,0) is at centre
        """
        if usePygame: #for pygame top left is 0,0
            lastPosPix = numpy.array(mouse.get_pos())
            #set (0,0) to centre
            lastPosPix[1] = self.win.size[1]/2-lastPosPix[1]
            lastPosPix[0] = lastPosPix[0]-self.win.size[0]/2
        else: #for pyglet bottom left is 0,0
            #use default window if we don't have one
            if self.win: w = self.win.winHandle
            else: w=pyglet.window.get_platform().get_default_display().get_windows()[0]       
            #get position in window
            lastPosPix= numpy.array([w._mouse_x,w._mouse_y])
            #set (0,0) to centre
            lastPosPix = lastPosPix-self.win.size/2
        self.lastPos = self._pix2windowUnits(lastPosPix)    
        return self.lastPos
            
    def mouseMoved(self, distance=None, reset=False):
        """Determine whether/how far the mouse has moved
        
        With no args returns true if mouse has moved at all since last getPos() call,
        or distance (x,y) can be set to pos or neg distances from x and y to see if moved either x or y that far from lastPos ,
        or distance can be an int/float to test if new coordinates are more than that far in a straight line from old coords.
        
        Retrieve time of last movement from self.mouseClock.getTime().
        
        Reset can be to 'here' or to screen coords (x,y) which allows measuring distance from there to mouse when moved.
        if reset is (x,y) and distance is set, then prevPos is set to (x,y) and distance from (x,y) to here is checked,
        mouse.lastPos is set as current (x,y) by getPos(), mouse.prevPos holds lastPos from last time mouseMoved was called
        """
        global mouseMove # clock that gets reset by pyglet mouse movement handler
        self.prevPos=copy.copy(self.lastPos) # needs initialization before getPos resets lastPos
        self.getPos() # sets self.lastPos to current position
        if not reset:
            if distance is None:
                    if self.prevPos[0] <> self.lastPos[0]: return True 
                    if self.prevPos[1] <> self.lastPos[1]: return True
            else: 
                    if isinstance(distance,int) or isinstance(distance,float):
                        self.movedistance=xydist(self.prevPos,self.lastPos)
                        if self.movedistance > distance: return True
                        else: return False
                    if (self.prevPos[0]+distance[0]) - self.lastPos[0] > 0.0: return True # moved on X-axis
                    if (self.prevPos[1]+distance[1]) - self.lastPos[0] > 0.0: return True # moved on Y-axis
            return False
        if isinstance(reset,bool) and reset:
            # reset is True so just reset the last move time, eg mouseMoved(reset=True) starts/zeroes the move clock
            mouseMove.reset() # resets the global mouseMove clock
            return False
        if reset=='here': # set to wherever we are
            self.prevPos=copy.copy(self.lastPos) # lastPos set in getPos()
            return False
        if hasattr(reset,'__len__'): # a tuple or list of (x,y)
            self.prevPos=copy.copy(reset) # reset to (x,y) to check movement from there
            if not distance: return False # just resetting prevPos, not checking distance
            else: # checking distance of current pos to newly reset prevposition
                if isinstance(distance,int) or isinstance(distance,float):
                    self.movedistance=xydist(self.prevPos,self.lastPos)
                    if self.movedistance > distance: return True
                    else: return False
                # distance is x,y tuple, to check if the mouse moved that far on either x or y axis 
                # distance must be (dx,dy), and reset is (rx,ry), current pos (cx,cy): Is cx-rx > dx ?
                if abs(self.lastPos[0]-self.prevPos[0]) > distance[0]: return True # moved on X-axis
                if abs(self.lastPos[1]-self.prevPos[1]) > distance[1]: return True # moved on Y-axis
            return False
        return False

    def mouseMoveTime(self):
        global mouseMove
        if mouseMove:
                return psychopy.core.getTime()-mouseMove.timeAtLastReset
        else: return 0 # mouseMove clock not started

    def getRel(self):
        """Returns the new position of the mouse relative to the
        last call to getRel or getPos, in the same units as the :class:`~visual.Window`.
        """
        if usePygame: 
            relPosPix=numpy.array(mouse.get_rel()) * [1,-1]
            return self._pix2windowUnits(relPosPix)
        else: 
            #NB getPost() resets lastPos so MUST retrieve lastPos first
            if self.lastPos is None: relPos = self.getPos()
            else: relPos = -self.lastPos+self.getPos()#DON't switch to (this-lastPos)
            return relPos
    
    def getWheelRel(self):
        """Returns the travel of the mouse scroll wheel since last call.
        Returns a numpy.array(x,y) but for most wheels y is the only
        value that will change (except mac mighty mice?)
        """
        global mouseWheelRel
        rel = mouseWheelRel
        mouseWheelRel = numpy.array([0.0,0.0])
        return rel

    def getVisible(self):
        """Gets the visibility of the mouse (1 or 0)
        """
        if usePygame: return mouse.get_visible()
        else: print "Getting the mouse visibility is not supported under pyglet, but you can set it anyway"
        
    def setVisible(self,visible):
        """Sets the visibility of the mouse to 1 or 0
        
        NB when the mouse is not visible its absolute position is held
        at (0,0) to prevent it from going off the screen and getting lost!
        You can still use getRel() in that case.
        """
        if usePygame: mouse.set_visible(visible)
        else:             
            if self.win: #use default window if we don't have one
                w = self.win.winHandle
            else: 
                w=pyglet.window.get_platform().get_default_display().get_windows()[0]  
            w.set_mouse_visible(visible)
    
    def clickReset(self,buttons=[0,1,2]):
        """Reset a 3-item list of core.Clocks use in timing button clicks.
           The pyglet mouse-button-pressed handler uses their timeAtLastReset when a button is pressed
           so the user can reset them at stimulus onset or offset to measure RT.
           The default is to reset all, but they can be reset individually as specified in buttons list
        """
        global mouseClick
        for c in buttons:
            mouseClick[c].reset()

    def getPressed(self, getTime=False):
        """Returns a 3-item list indicating whether or not buttons 1,2,3 are currently pressed
        
        If `getTime=True` (False by default( then `getPressed` will return all buttons that
        have been pressed since the last call to `mouse.clickReset` as well as their
        time stamps::
            
            buttons = mouse.getPressed()
            buttons, times = mouse.getPressed(getTime=True)        
        
        Typically you want to call :ref:`mouse.clickReset()` at stimulus onset, then 
        after the button is pressed in reaction to it, the total time elapsed 
        from the last reset to click is in mouseTimes. This is the actual RT,
        regardless of when the call to `getPressed()` was made.
        
        """
        global mouseButtons,mouseTimes
        if usePygame: return mouse.get_pressed()
        else:  #False: #havePyglet: # like in getKeys - pump the events
            #for each (pyglet) window, dispatch its events before checking event buffer
            wins = pyglet.window.get_platform().get_default_display().get_windows()
            for win in wins: win.dispatch_events()#pump events on pyglet windows

            #else: 
            if not getTime: return mouseButtons
            else: return mouseButtons, mouseTimes

    def _pix2windowUnits(self, pos):
        if self.win.units=='pix': return pos
        elif self.win.units=='norm': return pos*2.0/self.win.size
        elif self.win.units=='cm': return psychopy.misc.pix2cm(pos, self.win.monitor)
        elif self.win.units=='deg': return psychopy.misc.pix2deg(pos, self.win.monitor)
    def _windowUnits2pix(self, pos):
        if self.win.units=='pix': return pos
        elif self.win.units=='norm': return pos*self.win.size/2.0
        elif self.win.units=='cm': return psychopy.misc.cm2pix(pos, self.win.monitor)
        elif self.win.units=='deg': return psychopy.misc.deg2pix(pos, self.win.monitor)
        

class CustomMouse():
    """Class for more control over the mouse, including the pointer graphic and bounding box.
    
    Seems to work with pix or norm units, pyglet or pygame. Not completely tested.
    
    Known limitations:
    - getRel() always returns [0,0]
    - mouseMoved() is always False; maybe due to self.mouse.visible == False -> held at [0,0]
    - no idea if clickReset() works
    
    Would be nice to:
    - detect down-going or up-going mouse buttons, not just state-down, state-up (is-pressed vs was-clicked)
    - use the system mouse icon as the default mouse pointer
    
    Author: Jeremy Gray, 2011
    """
    def __init__(self, win, newPos=None, visible=True,
                 leftLimit=None, topLimit=None, rightLimit=None, bottomLimit=None,
                 showLimits=False,
                 pointer=None):
        """Class for customizing the appearance and behavior of the mouse.
        Create your `visual.Window` before creating a Mouse.
        
        :Parameters:
            win : required, `visual.Window`
                the window to which this mouse is attached
            visible : **True** or False
                makes the mouse invisbile if necessary
            newPos : **None** or [x,y]
                gives the mouse a particular starting position (pygame or pyglet)
            leftLimit :
                left edge of a virtual box within which the mouse can move
            topLimit :
                top edge of virtual box
            rightLimit :
                right edge of virtual box
            bottomLimit :
                lower edge of virtual box
            showLimits : False
                display the area within which the mouse can move.
            pointer :
                The visual display item to use as the pointer; must have .draw() and setPos() methods.
                If your item has .setOpacity(), you can alter the mouse's opacity.
        :Note:
            CustomMouse is a new feature, and as such is subject to change. Currently, getRel() returns [0,0]
            and mouseMoved() always returns False. clickReset() may not be working.
        """
        self.win = win
        self.mouse = Mouse(win=self.win)
        self.lastPos = None
        self.prevPos = None
        self.showLimits = showLimits
        # maybe just inheriting from Mouse would be easier?
        self.getRel = self.mouse.getRel
        self.getWheelRel = self.mouse.getWheelRel
        self.mouseMoved = self.mouse.mouseMoved  # FAILS
        self.mouseMoveTime = self.mouse.mouseMoveTime
        self.getPressed = self.mouse.getPressed
        self.clickReset = self.mouse.clickReset  # ???
        self._pix2windowUnits = self.mouse._pix2windowUnits
        self._windowUnits2pix = self.mouse._windowUnits2pix
        
        # the graphic to use as the 'mouse' icon (pointer)
        if pointer:
            self.setPointer(pointer)
        else:
            self.pointer = psychopy.visual.TextStim(win, text='+')
            #cursor = self.win.winHandle.get_system_mouse_cursor(self.win.winHandle.CURSOR_DEFAULT)
            #self.pointer = psychopy.visual.PatchStim(self.win,tex=numpy.array([[1]]),texRes=256,size=.04)
        self.mouse.setVisible(False) # hide the actual (system) mouse
        self.visible = visible # the custom (virtual) mouse
        
        self.leftLimit = None
        self.rightLimit = None
        self.topLimit = None
        self.bottomLimit = None
        self.setLimit(leftLimit=leftLimit, topLimit=topLimit, rightLimit=rightLimit, bottomLimit=bottomLimit)
        if newPos is not None:
            self.x, self.y = newPos
        else:
            self.x = self.y = 0
    def setPos(self, pos=None):
        """Place the mouse at a specific position (pyglet or pygame).
        """
        if pos is None:
            pos = self.getPos()
        self.pointer.setPos(pos)
    def getPos(self):
        """Returns the mouse's current position, as constrained to be within its virtual box.
        """
        dx, dy = self.getRel()
        self.x = min(max(self.x+dx, self.leftLimit), self.rightLimit)
        self.y = min(max(self.y+dy, self.bottomLimit), self.topLimit)
        self.lastPos = numpy.array([self.x, self.y])
        return self.lastPos
    def draw(self):
        """Draw mouse in the window if visible, plus showBox.
        """
        self.setPos()
        if self.showLimits:
            self.box.draw()
        if self.visible:
            self.pointer.draw()
        # we draw every frame, so here is good place to detect down-up state and update "clicks"
        
    def getVisible(self):
        return self.visible
    def setVisible(self, visible):
        """Make the mouse visible or not (pyglet or pygame).
        """
        self.visible = visible
    def setPointer(self, pointer):
        """Set the visual item to be drawn as the mouse pointer.
        """
        if 'draw' in dir(pointer) and 'setPos' in dir(pointer):
            self.pointer = pointer
        else:
            raise AttributeError, "need .draw() and setPos() methods in pointer"
    def setLimit(self, leftLimit=None, topLimit=None, rightLimit=None, bottomLimit=None):
        """Set the mouse's virtual box by specifying the edges.
        """
        if type(leftLimit) in [int,float]:
            self.leftLimit = leftLimit
        elif self.leftLimit is None:
            self.leftLimit = -1
            if self.win.units == 'pix':
                self.leftLimit = self.win.size[0]/-2.
        if type(rightLimit) in [int,float]:
            self.rightLimit = rightLimit
        elif self.rightLimit is None:
            self.rightLimit = 1
            if self.win.units == 'pix':
                self.rightLimit = self.win.size[0]/2.
        if type(topLimit) in [int,float]:
            self.topLimit = topLimit
        elif self.topLimit is None:
            self.topLimit = 1
            if self.win.units == 'pix':
                self.topLimit = self.win.size[1]/2.
        if type(bottomLimit) in [int,float]:
            self.bottomLimit = bottomLimit
        elif self.bottomLimit is None:
            self.bottomLimit = -1
            if self.win.units == 'pix':
                self.bottomLimit = self.win.size[1]/-2.
        
        self.box = psychopy.visual.ShapeStim(self.win,
                    vertices=[[self.leftLimit,self.topLimit],[self.rightLimit,self.topLimit],
                        [self.rightLimit,self.bottomLimit],
                        [self.leftLimit,self.bottomLimit],[self.leftLimit,self.topLimit]])
        
        # avoid accumulated relative-offsets producing a different effective limit:
        self.mouse.setVisible(True)
        self.x, self.y = self.mouse.getPos()
        self.mouse.setVisible(False)
        
class KeyResponse:
    def __init__(self):
        self.keys=[] #the key(s) pressed
        self.corr=0 #was the resp correct this trial? (0=no, 1=yes)
        self.rt=None #response time
        self.clock=psychopy.core.Clock() #we'll use this to measure the rt
        self.clockNeedsReset = True
        
def clearEvents(eventType=None):
    """Clears all events currently in the event buffer.
    Optional argument, eventType, specifies only certain types to be
    cleared 
    
    :Parameters:
        eventType : **None**, 'mouse', 'joystick', 'keyboard' 
            If this is not None then only events of the given type are cleared
    """
    #pyglet
    if not havePygame or not display.get_init():
        
        #for each (pyglet) window, dispatch its events before checking event buffer    
        wins = pyglet.window.get_platform().get_default_display().get_windows()
        for win in wins: win.dispatch_events()#pump events on pyglet windows
        if eventType=='mouse': return # pump pyglet mouse events but don't flush keyboard buffer
        global _keyBuffer
        _keyBuffer = []
        return
    
    #for pygame
    if eventType=='mouse':
        junk = evt.get([locals.MOUSEMOTION, locals.MOUSEBUTTONUP,
                        locals.MOUSEBUTTONDOWN])
    elif eventType=='keyboard':
        junk = evt.get([locals.KEYDOWN, locals.KEYUP])
    elif eventType=='joystick':
        junk = evt.get([locals.JOYAXISMOTION, locals.JOYBALLMOTION, 
              locals.JOYHATMOTION, locals.JOYBUTTONUP, locals.JOYBUTTONDOWN])
    else:
        junk = evt.get()
