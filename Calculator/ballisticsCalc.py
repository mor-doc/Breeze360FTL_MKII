from numpy import ndarray, array, deg2rad, rad2deg, eye, sin, cos, matmul, transpose, vstack, arctan2, mod
from numpy.linalg import inv, norm
from scipy.optimize import fsolve
from operator import itemgetter

import cannonConstants as ccon
from cannonConstants import cardinalDir

def rotateCoord(startDir: cardinalDir, endDir: cardinalDir, coordVec: ndarray) -> ndarray:
    """
    Rotate coordinate by azimuth from starting to final cardinal direction. 
    Example:
        rotateCoord(NORTH, EAST, [1, 0, 0]) => [0, 0, 1]

    Args:
        startDir (cardinalDir): initial facing direction
        endDir (cardinalDir): final facing direction
        coordVec (ndarray): 1x3 vector to be rotated

    Returns:
        ndarray: 1x3 vector facing new direction
    """
    angleCCW = (endDir.value - startDir.value) * 90
    angleRad = deg2rad(angleCCW)
    rotMatrix = eye(3)
    rotMatrix[0][0] = rotMatrix[2][2] = cos(angleRad)
    rotMatrix[0][2] = sin(angleRad)
    rotMatrix[2][0] = -sin(angleRad)
    return matmul(coordVec, rotMatrix)

def pearlInitVelFromEndPos(tick: int, displacement: ndarray) -> ndarray:
    """
    Get initial velocity to get required ender pearl displacement after some time
    (see wiki for formula)

    Args:
        tick (int): flight time from trajectory start in gameticks
        displacement (ndarray): target displacement as 1x3 vector

    Returns:
        ndarray: initial velocity as 1x3 vector
    """
    
    d = ccon.dragCoeff
    a = ccon.gravityAccel
    return (1 - d) / (d * (1 - pow(d, tick))) * (displacement - d * tick * a / (1 - d)) + (d / (1 - d) * a)

def pearlPosFromInitVel(tick: float, vel0: ndarray) -> ndarray:
    """
    Get ender pearl displacement from initial velocity after some time
    (see wiki for formula)

    Args:
        tick (float): time from trajectory start in gameticks
        vel0 (ndarray): initial velocity as 1x3 vector

    Returns:
        ndarray: displacement relative to starting point as 1x3 vector
    """

    d = ccon.dragCoeff
    a = ccon.gravityAccel
    return (d * (1 - pow(d, tick))) / (1 - d) * (vel0 - d / (1 - d) * a) + (d * tick * a / (1 - d))

def getExplosionMatrix(velA:ndarray, velB:ndarray) -> ndarray:
    """
    Get E matrix from two 3D explosion velocity vectors
    (see tutorial wiki page)

    Args:
        velA (ndarray): velocity from first explosion as 1x3 vector
        velB (ndarray): velocity from second explosion as 1x3 vector

    Returns:
        ndarray: 2x3 E matrix
    """
    
    velMatrix = transpose(vstack((velA, velB)))
    A = matmul(transpose(velMatrix), velMatrix)
    B = inv(A)
    C = matmul(B, transpose(velMatrix))
    return C

def getChargePearlPushVelocity(explosionCenterPos: ndarray, pearlFeetPos: ndarray) -> ndarray:
    """
    Calculate impulse to ender pearl from one wind charge explosion. 
    Assumes 100% exposure 
    (see Explosion wiki page for formulas)

    Args:
        explosionCenterPos (ndarray): position of wind charge explosion as 1x3 vector
        pearlFeetPos (ndarray): position of ender pearl feet (reported position) as 1x3 vector

    Returns:
        ndarray: velocity change as 1x3 vector (away from wind charge)
    """
    
    feetDist = pearlFeetPos - explosionCenterPos
    WindChargePower = 3.0
    exposure = 1.0    
    magnitude = (1 - norm(feetDist) / (2 * WindChargePower)) * exposure
    eyeVector = feetDist + ccon.pearlEyeOffset
    velocityVector = eyeVector / norm(eyeVector) * magnitude
    return velocityVector

def findChargeAmount(velA: ndarray, velB: ndarray, targetOffs: ndarray) -> ndarray:
    """
    Solve for wind charge stack sizes and flight time

    Args:
        velA (ndarray): velocity added to ender pearl from one wind charge in position A. Format - 1x3 vector
        velB (ndarray): velocity added to ender pearl from one wind charge in position B. Format - 1x3 vector
        targetOffs (ndarray): relative offset from initial pearl position to target

    Returns:
        ndarray: nearest solution as 1x3 vector of floats. 
            Element 0 - flight time (in gameticks). Element 1 - size of charge stack A. Element 2 - size of charge stack B.
    """
    
    # idea - use gameticks as another variable, 3 total. Return full pos error
    def optimizeFunc(x):
        tick, amtA, amtB = x
        velVector = amtA * velA + amtB * velB
        velVector += ccon.pearlInitialVelocity
        pearlPos = pearlPosFromInitVel(tick, velVector)
        posError = targetOffs - pearlPos
        return posError
    result = fsolve(optimizeFunc, [1.0e9, 0, 0])
    
    return result # type: ignore

def getLocalQuadData(targetOffs : ndarray) -> tuple[int, ndarray, ndarray]:
    """
    Get shooting quadrant info from target position offset

    Args:
        targetOffs (ndarray): target position relative to acceleration zone in cannon-local frame

    Returns:
        tuple[launchQuadId, ndarray, ndarray]: id of quadrant inside aligner, position of first charge stack, position of last charge stack
    """
    
    # Issue - quad boundaaries are wrong, on some edge cases gives negative charges
    
    targetAngleDeg = mod(rad2deg(arctan2(targetOffs[2], targetOffs[0])) + 360, 360)
    
    # Make array with angles and indices, like in Excel (must be sorted to ascending angle)
    quadAngleArr = list()
    for i in range(4):
        angle = rad2deg(arctan2(
            ccon.chargePositions[i][2] - ccon.pearlPosition[2],
            ccon.chargePositions[i][0] - ccon.pearlPosition[0] 
            )) + 180
        quadId = i
        quadAngleArr.append((quadId, angle))
        quadAngleArr.append((quadId, angle - 360))
        quadAngleArr.append((quadId, angle + 360))
    quadAngleArr.sort(key=itemgetter(1))
    
    # Iterate over array, search for first value >= target angle, read its index
    nextQuad = 0
    for (i, ang) in quadAngleArr:
        if(ang >= targetAngleDeg):
            nextQuad = i
            break
    # Get next quadrant index from this index
    thisQuad = (nextQuad - 1) % 4
    
    # Assign first and least stacks - flip order depending on quad number
    cwStack = ccon.chargePositions[nextQuad]
    ccwStack = ccon.chargePositions[thisQuad]
    alignerQuad = (thisQuad + 1) % 4
    if(alignerQuad == 0):
        return (alignerQuad, ccwStack, cwStack)
    else:
        return (alignerQuad, cwStack, ccwStack)

def calculateLaunchParameters(cannonDir : cardinalDir, cannonPos: ndarray, targetPos: ndarray) -> tuple[int, int, int, int, ndarray]:
    """
    Calculate launch parameters for the cannon to hit near the target

    Args:
        cannonDir (cardinalDir): cardinal direction taken looking at item frame
        cannonPos (ndarray): absolute position of block behind item frame as 1x3 vector
        targetPos (ndarray): absolute target position as 1x3 vector

    Returns:
        tuple[launchQuadId, int, int, int, ndarray]: launch parameters:
            - index of quadrant to select with item frame (0 is bottom-left, 3 is bottom-right)
            - flight time in gameticks
            - number of wind charges in first stack
            - number of wind charges in last stack
            - nearest possible coordinates to target
    """

    shootingPos = cannonPos + rotateCoord(ccon.defaultFacingDir, cannonDir, ccon.itemToOriginOffset)
    globalTargetOffset = targetPos - shootingPos
    localTargetOffset = rotateCoord(cannonDir, ccon.defaultFacingDir, globalTargetOffset)

    quadId, stackPosA, stackPosB = getLocalQuadData(localTargetOffset)
    velA = getChargePearlPushVelocity(stackPosA, ccon.pearlPosition)
    velB = getChargePearlPushVelocity(stackPosB, ccon.pearlPosition)
    idealCannonSetting = findChargeAmount(velA, velB, localTargetOffset)
    # Get realistic values, check rounding error
    ticks, chargesA, chargesB = idealCannonSetting.round()
    velVector = chargesA * velA + chargesB * velB
    actualLocalOffs = pearlPosFromInitVel(ticks, velVector)
    actualLandingPos = shootingPos + rotateCoord(ccon.defaultFacingDir, cannonDir, actualLocalOffs)
    
    # quadId must be flipped for UI due to orientation of launch area (minor bug of quad input device)
    return ((quadId + 2) % 4, int(ticks), int(chargesA), int(chargesB), actualLandingPos)
