#!/usr/bin/env python3
from PIL import Image
import qrcode
import numpy as np
from numpy.linalg import inv
import itertools

'''
NOTE:
color-tuples are 3 element tuples structred as (R,G,B), 0-255 each

point-tuples are 2 element tuples structed as (x,y)
(note that this is consistent with pillows use of points)
vectors are equivalent to point-tuples, but with a different context

quadrilateral-tuples are 4 element tuples structured as (point-tuple,point-tuple,point-tuple,point-tuple)
'''

def addTuples(t1, t2):
	'''
	@params:
		t1 is a tuple
		t2 is a tuple
	Adds the contents of each tuple, element by element.
	EX: addTuples((1,2),(4,6)) -> (5,8)
	@jacob
	'''
	return piecewiseMap(t1, t2, lambda x,y: x+y)

def piecewiseMap(t1, t2, fn):
	'''
	@params:
		t1 is a tuple
		t2 is a tuple
		fn is a function taking two parameters, and returning a single value
	Maps corresponding params of t1 and t2 by index.
	Calls supplied function as fn(t1[i], t2[i]) for each i in len(tuples)
	Returns a tuple of min((len(t1), len(t2)))
	'''
	return tuple(fn(x,y) for x,y in zip(t1,t2))

def diffColors(a, b):
	'''
	@params:
		a is a color-tuple
		b is a color-tuple

	Yield an integer value representing total difference among color values.
	Difference is computed for each R, G, B of color
	Ranges from 0 (same color) to 765 (max difference)
	'''
	return sum(abs(x - y) for x,y in zip(a,b))


def diffPoints(image, p1, p2):
	'''
	@params:
		image is the PIL image to sample from
		p1 is a point-tuple
		p2 is a point-tuple

	Delegate call to diffColors on two points in an image
	'''
	a = image.getpixel(p1)
	b = image.getpixel(p2)
	return diffColors(a,b)

def getPixelClusters(image, start, direction):
	'''
	@params:
		image is the PIL image to sample from
		start is a point-tuple defining where to begin scanning clusters
		direction is a vector defining direction to travel

	Scan over an image from a starting point until end of image is reached.
	Scan results are returned as a list of tuples containing the start point of
	the cluster, and the length of that cluster.
	EX:
	[((5,0), 15), ((5,15), 7), ...]
	   ^--point-tuple      ^--length of cluster

	direction as a vector allows this function to be used for vertical, horizontal,
	diagonal, or any angle of traversal, at varying levels of precision.
	'''
	ret_vals = [] #Create list to add clusters to
	last_point = start
	next_point = addTuples(last_point, direction)

	#Track current cluster
	cluster_start = last_point
	cluster_size = 1

	threshold = 50
	#Continue scanning until curr_point is outside of image
	while isInBounds(image, next_point):
		delta = diffPoints(image, last_point, next_point)

		#Check if delta below thresh; if so, Continue
		if delta < threshold:
			cluster_size += 1
		else:
			#Else, add to ret vals
			ret_vals += [(cluster_start, cluster_size)]
			cluster_start = next_point
			cluster_size = 1

		last_point = next_point
		next_point = addTuples(last_point, direction)

	#Add last value to clusters
	ret_vals += [(cluster_start, cluster_size)]
	return ret_vals


def findQR(image):
	'''
	@params:
		image is the image that we'll be messing with
	Returns n quadrilateral-tuples where n is the number of QR codes in the image.
	'''
	clusters = getPixelClusters(image)
	pass #@todo(someone) finish this


def insertQR(image, bounds, data):
	'''
	@params:
		image is the image that we'll be messing with
		bounds is a quadrilateral-tuple specifying where to place the image
		data is what will be encoded in the QR code
	inserts a QR code into the image at the specified bounds
	the new qr code should fit the bounds and seem natural (like it was the original imge)
	'''
	pass #@todo(someone) implement this

def isInBounds(image, point):
	'''
	@params:
		image is the image that we'll be messing with
		point is a tuple-point that we are testing
	returns a boolean
		True if the point is inside the image
		False if the point is outside the image
	'''
	width, height = image.size
	p = point
	return p[0] >= 0 and p[1] >= 0 and p[0] < width and p[1] < height
	#return all([dim > loc for dim,loc in zip(size,point)]) #jacob wrote this hideous line of code and said fight me and its bad
	#return all([size[i] > point[i] for i in range(2)]) or min(point) =< 0

def distance(a, b):
	'''
	@params:
		a is a point-tuple
		b is another point-tuple
	returns a double representing distance between the two points
	'''
	return math.hypot(a.x - b.x, a.y - b.y)

def angleOf(vector):
	'''
	@params:
		vector is a vector-tuple
	returns a double representing the vectors clockwise rotation from the x axis
		values range from [0,2pi)
	'''
	at = atan(vector[1], vector[0])
	if at < 0:
		at += 2*math.pi
	return at

def clockwiseRotation(from_v, to_v):
	'''
	@params:
		from_v is a vector-tuple
		to_v is a vector-tuple
	returns a double representing the total rotation from vector from_v
		to the vector to_v. Value returned is in range [0,2pi).
		Used to determine which point is the "upper" clockwise leg of a triangle
	'''
	a = angleOf(from_v) - angleOf(to_v)
	if a < 0`:
		a += 2 * math.pi
	return a

def extrapolateParallelogramJ(a, b, c):
	'''
	@params:
		a is one of the detected clusters in the image
		b ditto
		c ditto
	returns a list of four points representing vertices of parallelogram
		in clockwise order. The new point is generated based on the previous 3.
	'''

	def deduceKnownCorner(a, b, c): #Get points as (corner, another, another)
		segs = ((a,b), (b,c), (a,c))
		sorted_distance = sorted(segs, key=lambda seg: distance(seg[0], seg[1]))
		longest_seg = sorted_distance[2]
		return sorted((a,b,c), key=lambda p: p in longest_seg)

	def orderByRotation(a, b, c): #Orders points of triangle clockwise. First point is anchor. Tuple of tuple-point
		cp = deduceKnownCorner(a,b,c)
		corner = cp[0]
		a = cp[1]
		b = cp[2]

		#Get vectors from corner to each leg
		v_corner_a = piecewiseMap(corner, a, lambda x,y: y - x)
		v_corner_b = piecewiseMap(corner, b, lambda x,y: y - x)

		#Find which comes vector 'first', clockwise from x axis
		#Determined by which has lower clockwise angle
		rab = clockwiseRotation(v_corner_a, v_corner_b)
		rba = clockwiseRotation(v_corner_b, v_corner_a)

		if rab < rba:
			return (corner, a, b)
		else:
			return (corner, b, a)

	def genThirdPoint(ordered_points): #Takes result of orderByRotation, returns final point
		#Just generate a parallelogram u dingaling
		corner = ordered_points[0]
		leg1 = ordered_points[1]
		leg2 = ordered_points[2]
		vec_corner_leg1 = piecewiseMap(corner, leg1, lambda x,y: y - x)

		#Add this vec to leg2 to get final point of pgram.
		return addTuples(leg2, vec_corner_leg1)

	op = orderByRotation(a,b,c)
	np = genThirdPoint(op)
	return (op[0], op[1], np, op[2])

def extrapolateParallelogram(a, b, c):
	'''
	@params:
		a is one point-tuple in the parallelogram
		b is another point-tuple
		c is the third point-tuple
	returns a list of four points representing vertices of parallelogram
		formed by the points, that most closely resembles a square
		i.e. [(xa,ya), (xb,yb), (xc,yc), (xd,yd)]
		points are returned in sorted order(first by x then y if x's tie)
	'''
	dist = [distance(a,b), distance(b,c), distance(a,c)]
	maxIndex = dist.index(max(dist))

	#determine which side is longest, so we can find which direction to go
	if maxIndex == 0:
		point1, point2, point3 = a,b,c
	if maxIndex == 1:
		point1, point2, point3 = b,c,a
	if maxIndex == 2:
		point1, point2, point3 = a,c,b

	#find all possile new points from vector addition, and see which two are equal
	p1 = addTuples(tuple(x-y for x,y in zip(point1, point3)), point2)
	p2 = addTuples(tuple(y-x for x,y in zip(point1, point3)), point2)
	p3 = addTuples(tuple(x-y for x,y in zip(point2, point3)), point1)
	p4 = addTuples(tuple(y-x for x,y in zip(point2, point3)), point1)

	#if they're equal, that's the new point.
	if p1 == p4:
		point4 = p1
	if p1 == p3:
		point4 = p1
	if p2 == p4:
		point4 = p2
	if p2 == p3:
		point4 = p2

	parallelogram = (point1, point2, point3, point4)

	return sorted(parallelogram)


def warpImage(background, image, parallelogram):
	'''
	@params:
		background is unchanged image
		image is image to be warped
		parallelogram is the coordinates to warp the image to, starting at upper
			left and going clockwise
	returns a new image that is the composition of background and image
	 	after image has been warped
	'''
	mapped = np.array([[parallelogram[0][0], parallelogram[1][0], parallelogram[2][0]],
	[parallelogram[0][1], parallelogram[1][1], parallelogram[2][1]], [1,1,1]])
	width, height = image.size
	original = np.array([[0, width, width],[0, 0, height]])
	#solve for affine matrix
	solution = np.dot(original, inv(mapped))
	#unroll matrix into a sequence
	affine = (solution[0][0], solution[0][1], solution[0][2], solution[1][0], solution[1][1], solution[1][2])
	transformed = image.transform(background.size, Image.AFFINE, affine)
	white = Image.new("RGBA", (width, height), "white")
	transformedMask = white.transform(background.size, Image.AFFINE, affine)
	background.paste(transformed, (0,0), transformedMask)
	return background

def scanImage(image):
	'''
	@params
		image is the image that we'll be messing with
	returns a list of tuple-points which are the centers of any QR code corner identifiers
	'''
	lineclusters = []
	for i in range(image.size[1]): #goes through each row of pixels in the image
		lineclusters.append(getPixelClusters(image,(0,i),(1,0))) #grabs the clusters from one line

	iclusters = [] #interesting clusters
	for line in lineclusters:
		matches = []
		for i in range(len(lineclusters)-4): #scan the clusters five at a time to find the QR pattern
			scanthis = line[i:i+5]			 #we're looking for 1-1-3-1-1
			baselen = len(scanthis[0])
			if kindaEquals(baselen, scanthis[1][1]) and kindaEquals(baselen, scanthis[3][1]) and kindaEquals(baselen, scanthis[4][1]) and kindaEquals(baselen*3, scanthis[2][1]): #i'm so sorry for this line of code. basically it just checks for the 1 1 3 1 1 pattern in qr code corners
				matches.append(scanthis[3][1]/2 + scanthis[3][1][0]) #adds the middle of the middle of the scan to the matches
		iclusters.append(matches)

	cluster_points = [] #this is a list of cluster points that we will be returning
	current_line = -1 #we start at -1 because i do +1 at the beginning
	while current_line < image.size[1]:
		current_line = current_line + 1
		continue if len(lineclusters[current_line]) < 0 #so that i can just do this lazy line of code
		for current_col in lineclusters[current_line] #this for loop handles when there's two clusters in one row (bottom of QR code)
			scanline = current_line #we sometimes need to scanline down twice
			while len(lineclusters[scanline] > 0) and lineclusters[scanline] kindaEquals(current_line): #make sure that the clusters match up
				scanline = scanline + 1
			cluster_center = (current_col, int((scanline - current_line)/2)) #current_col is the position in the row
			cluster_points.append(cluster_center)							#scanline is end of the cluster, current_line is beginning so we can take their mean to get the middle
		current_line = scanline #after scanning the clusters we set current line to scanline
									#if we get lots of very nearby points change previous line to blabla = scanline + 1
	return cluster_points



def kindaEquals(num1, num2, leniency=.2):
	'''
	@params
		num1 is a number
		num2 is also a number
		leniency is how lenient you're willing to be
	returns a boolean
		true if num1 is pretty close to num2
		false is num1 is pretty far from num2
	'''
	n2_max = num1*(1+leniency)
	n2_min = num1*(1-leniency)
	return num1 == num2 or n2 < n2_max and n2 > n2_min
