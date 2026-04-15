from numpy import array
from enum import Enum

# Enum for Minecraft world directions. East is +X, South is +Z.
class cardinalDir(Enum):
    NORTH = 2
    EAST = 3
    SOUTH = 0
    WEST = 1

# Array of wind charge positions relative to launch zone center. 
# Assumes that charge stacks enter in bottom-left corner (from East / positive X). 
chargePositions = array([
    [-0.83375, 0.75, -0.16625],      # earliest pos in spiral
    [+0.16625, 0.75, -0.84375], 
    [+0.84375, 0.75, +0.16625], 
    [-0.16625, 0.75, +0.84375]       # latest pos in spiral (gets inside 1st block)
    ])

# Facing direction of cannon in default orientation. 
# Taken by looking at item frame
defaultFacingDir = cardinalDir.SOUTH

# Offset from block behind item frame to center of 2x2 explosion area
# In default facing direction, areaPos = itemFramePos + offset
itemToOriginOffset = array([15, 38, -2])

# Coordinate of ender pearl (feet pos) at the moment of explosion, relative to 2x2 area center. 
# Same orientation as wind charge coordinates
pearlPosition = array([+0.0625, 0.540222006, -0.0625])

# Offset from ender pearl feet pos to eye pos. Used for acceleration vector calculation
pearlEyeOffset = array([0, 0.2125, 0])

# Pearl velocity at the moment of explosion
pearlInitialVelocity = array([0.0, -0.00372668019444022, 0.0])

# Acceleration of pearl by gravity
gravityAccel = array([0, -0.03, 0])

# Velocity drag coefficient for pearl
dragCoeff = 0.9900000095367432
