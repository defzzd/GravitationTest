import math
import pygame
import os


#### Goal Statement ####

## This program is intended to test a very simple model of gravitic attraction.
## The way it works is as follows:
## Every update, each object with gravity would tell each other update with gravity to adjust their velocities by a tiny amount in the direction of that object.
## Then all the objects would move according to their velocity values.


## - Objects touching eachother should not move (( yet ))
## - Use the fp-int split between movement-calculation locations and pixel locations from Arinoid for movement calculations
## - You may also want to preempt rounding errors by using the max_speed stuff from Asteroids, since tiny numbers from the inverse square law might create numerical instabilities



#### Constants ####

## Is technically also the playing field --v
SCREEN_BOUNDARY_RECTANGLE = pygame.Rect(0, 0, 1200, 700)

WINDOW_CAPTION = 'Gravitation version 0.3'

MAX_FRAMES_PER_SECOND = 60

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

#### Classes ####


class Spritesheet:
	''' Loads spritesheets for graphical display purposes. '''
	
	## An easily reusable, general-purpose class for working with sprites in pygame!
	
	def __init__(self, supplied_filename):
		
		## Load the file and save it as a variable in this object.
		## os.path.join() appends the path in the directory tree to the name of the file call.
		## ((  I think join() returns a joined string, and os.path (???) sets or supplies a path to access a file, which is what's being requested as a parameter for pygame.image.load()  ))
		## Operating system-independent.
		## Also, convert() the data to the correct pixel format so pygame can use it quickly.
		self.sheet_file = pygame.image.load(os.path.join('folder containing data for GravitationTest', supplied_filename)).convert()


	def get_an_image_from_this_spritesheet(self, image_rectangle_measurements, colorkey=None):
		''' Create a pygame.Surface() holding a rectangular slice of a spritesheet from specified coordinates; can incorporate transparency. Return that pygame.Surface() '''
		
		## First, turn the numbers describing the rectangular area on the spritesheet into a pygame.Rect() object, which we call the image_slice_rectangle.
		image_slice_rectangle = pygame.Rect(image_rectangle_measurements)

		## Then create an empty pygame.Surface() and convert() it to the pygame pixel format.
		## Uses the image_slice_rectangle as a size, because that's what's going in this buffer!
		image_slice_buffer = pygame.Surface(image_slice_rectangle.size)

		## Transfer (blit) the area of self.sheet_file (the spritesheet) described by image_slice_rectangle onto the image_slice_buffer ( perfectly matching upper left corners with (0, 0) ).
		image_slice_buffer.blit(self.sheet_file, (0, 0), image_slice_rectangle)
		
		## Using transparency:
		## By default, the image will not be transparent in any part. That's the colorkey=None in the parameters for this function.
		if colorkey is not None:
		
			if colorkey is -1:
				## If we pass -1 as a colorkey, the game will use the color of the pixel in the upper left corner as its transparency-defining color.	
				## assigned_colorkey_variable = foo_image.get_at((x, y)) gets the color of the pixel at (x, y) in the image it's called on, and returns it as the assigned_colorkey_variable
				colorkey = image_slice_buffer.get_at((0, 0))
		
			## Otherwise, colorkey will use whatever argument is passed to it as a user-specified transparency color for this sprite/image slice/thing.
			
			## The flag RLEACCEL does something to make using the resulting image faster.
			##    v--- from http://www.pygame.org/docs/ref/surface.html
			## " The optional flags argument can be set to pygame.RLEACCEL to provide better performance on non accelerated displays. An RLEACCEL Surface will be slower to modify, but quicker to blit as a source. "
			
			image_slice_buffer.set_colorkey(colorkey, pygame.RLEACCEL)
		
		## Note: The returned object is a pygame.Surface()
		return image_slice_buffer
		

	def get_multiple_images_from_this_spritesheet(self, supplied_image_rectangle_measurements, colorkey=None):
		''' Create a list populated by pygame.Surface() objects -- i.e., images -- made using the get_an_image_from_this_spritesheet(image_rectangle_measurements, colorkey) function. Parameters require one to many rectangles and zero to one colorkeys. '''
		
		## NOTE: The tutorial had colorkey's default set to None, but that did not go over so well with new .bmp sheets for some reason, so I'm forcing it to use the 0,0 colorkey from now on.
		
		## First make an empty list to be filled with images, each of which is a pygame.Surface()
		list_of_images = []
		
		## Iterate through the rectangle measurements handed to this function, and append pygame.Surface() objects generated with get_an_image_from_this_spritesheet() to the list_of_images for each one.
		for each_rectangle_measurement in supplied_image_rectangle_measurements:
			list_of_images.append(self.get_an_image_from_this_spritesheet(each_rectangle_measurement, colorkey))
		
		## Once again, to be clear for beginners like me: This function returns a list full of pygame.Surface() objects.
		return list_of_images
		


		
		
	
class GravityWell(pygame.sprite.Sprite):
	''' Planets and stuff. They should both affect and be affected by gravity. '''
	
	## The way this is going down is as follows:

	## - Every GravityWell has an x_location and a y_location
	## - - This will use self.rect.centerx and self.rect.centery
	## - Every GravityWell has an x_velocity and a y_velocity
	## - Every GravityWell has a mass

	## - Every time update() is called on a GravityWell, it will For-loop over the entire group_of_gravity_wells
	## - - If it finds itself while iterating over the group_of_gravity_wells, it will skip itself and go to the next GravityWell
	## - For every GravityWell, it will determine the sine and cosine of the hypotenuse formed by the distance between the two GravityWells' centers
	## - Then it finds another ratio, the inverse_square_ratio, which is equal to ( 1 / (the_distance_between_them ** 2) )
	## - It will then multiply its mass value by the inverse_square_ratio, coming to a much smaller number, the gravitic_acceleration_value
	## - Then the gravitic_acceleration_value will be multiplied by both the sine and cosine to generate the new x_acceleration and y_acceleration values, depending on which is needed for which.
	## - I'll also figure out if multiplication by -1 is needed at that point, if that calculation comes to a repulsive gravity instead of an attractive one.
	
	## NOTE: Because it is not specific to any particular GravityWell, but rather acts on all of them once per RenderUpdates(), calculate_gravity_and_adjust_velocities_on_all_gravity_wells() is a top-level function.
	
	def __init__(self, initial_x_position, initial_y_position, initial_x_velocity, initial_y_velocity, initial_mass, is_immobile=False):
	
	
		pygame.sprite.Sprite.__init__(self, self.sprite_groups_this_object_is_inside)
	
		
		## EVEN THOUGH GravityWell doesn't actually accept graphix, all of its inheritor classes will, so this should still go through. Right?
			## DEBUG -- skip this, see if it matters to put it in Planet instead of GravityWell
			#	## The fact I called pygame.sprite.Sprite.__init__() before self.image.get_rect() means that the inheritor class's image will be initialized. Right??
			#	self.rect = self.image.get_rect()
		
		
		self.rect.centerx = initial_x_position
		self.rect.centery = initial_y_position
		
		self.current_x_velocity = float(initial_x_velocity)
		self.current_y_velocity = float(initial_y_velocity)
		
		self.current_mass = initial_mass
	
		self.is_immobile = is_immobile
	
		## When a GravityWell is spawning in, make sure you float its values for accurate mathings:
		self.convert_centerx_and_centery_to_floating_point()
	
		
		## This feels so, so wrong, but I know it'll work. May all the gods of programming forgive me.
		self.x_velocity_buffer = 0.0
		self.y_velocity_buffer = 0.0
		
	
		
		#debug3
		self.convert_centerx_and_centery_to_floating_point()
		
		
	def convert_centerx_and_centery_to_floating_point(self):
		''' Convert self.rect.centerx and self.rect.centery to floating point numbers for smoother ball movement calculations. '''
		
		## Pixels don't come in fractions. This method will be used to switch between floating point numbers and integers on the fly for smoother ball movement, giving more detail to the physics engine.
		## (( float() is a built-in Python function, as is int() ))
		self.floating_point_rect_centerx = float(self.rect.centerx)
		self.floating_point_rect_centery = float(self.rect.centery)
		
	def set_centerx_and_centery_values_to_ints_of_the_floating_point_values(self):
		''' Set self.rect.centerx and self.rect.centery to the self.floating_point_rect_centerfoo numbers for each. '''
		
		## Turns the floating point numbers from the above method into ints for pygame's Rect class's various pixel purposes.
		
		## This is a CRITICAL PART of moving things that store their x, y locations as floats!
		
	
		
		self.rect.centerx = int(self.floating_point_rect_centerx)
		self.rect.centery = int(self.floating_point_rect_centery)
		
	

	def update(self):
		''' In addition to normal update() stuff ((if there is any now that I'm redefining this function)), move the GravityWell object according to its current_x_velocity and current_y_velocity values. '''
		
		## NOTE: "update" implies we are updating THIS OBJECT. Only.
		## calculate_gravity_and_adjust_velocities_on_all_gravity_wells() is a top-level function that processes BEFORE RenderUpdates() in the game loop.
		
		
		
		
		#### THIS IS ALSO THE MOVE FUNCTION FOR NOW, POSSIBLY ALSO FOR ALWAYS ####

		
		## The GravityWell shouldn't go out of the playing_field_rectangle, so restrict it to the playing_field_rectangle using pygame's built-in clamp_ip() function, to "clamp in place" (?) the sprite inside the playing_field_rectangle given to its class as a reference variable.
		
		## DEBUG take 3: reenable clamping later
		
		#self.rect.clamp_ip(self.playing_field.playing_field_rectangle)
		
		## Also it needs to be refloated AFTER being clamped. Do not change the order of [[ clamp_ip() --> convert... --> movement code --> set_center... ]]
		
		#debug3
		#self.convert_centerx_and_centery_to_floating_point()
		
		
		
		## This is the part that seems so horribly wrong.
		## The purpose of this disaster is to try and make fractions of a pixel worth of velocity smoothly affect movement.
		## The buffer stores clipped values from -1 to +1.
		## If abs(current_velocity) < 1:
		## add the acceleration to the buffer
		## If abs(buffer) > 1:
		## add 1 to the_proper_center_axis, AND subtract 1 from the buffer
		## If abs(current_velocity) > 1:
		## 		add the buffer to current_acceleration AND zero the buffer
	
		if not self.is_immobile:
			## x buffer
			if (self.current_x_velocity < 1.0) and (self.current_x_velocity > -1.0):
				self.x_velocity_buffer += self.current_x_velocity
			
			if (self.x_velocity_buffer >= 1.0) or (self.x_velocity_buffer <= -1.0):
				## Velocity buffer overflow. Increment position.
				
				## note: a number divided by the abs. of itself gives either +1 or -1 depending on its original sign (it preserves its sign)
				self.floating_point_rect_centerx += (self.x_velocity_buffer / abs(self.x_velocity_buffer))
				if (self.x_velocity_buffer / abs(self.x_velocity_buffer)) == -1.0:
					self.x_velocity_buffer += 1.0
				else:	
					self.x_velocity_buffer -= 1.0
					
				#self.x_velocity_buffer -= (self.x_velocity_buffer / abs(self.x_velocity_buffer))
		
			
			if (self.current_x_velocity > 1.0) and (self.current_x_velocity < -1.0):
				self.x_velocity_buffer = 0.0
		
			## y buffer
			if (self.current_y_velocity < 1.0) and (self.current_y_velocity > -1.0):
				self.y_velocity_buffer += self.current_y_velocity
			
			if (self.y_velocity_buffer >= 1.0) or (self.y_velocity_buffer <= -1.0):
				## Velocity buffer overflow. Increment position.

					
				## note: a number divided by the abs. of itself gives either +1 or -1 depending on its original sign (it preserves its sign)
				self.floating_point_rect_centery += (self.y_velocity_buffer / abs(self.y_velocity_buffer))
				if (self.y_velocity_buffer / abs(self.y_velocity_buffer)) == -1.0:
					self.y_velocity_buffer += 1.0
				else:
					self.y_velocity_buffer -= 1.0
				
				#self.y_velocity_buffer -= (self.y_velocity_buffer / abs(self.y_velocity_buffer))
		
				
			if (self.current_y_velocity > 1.0) and (self.current_y_velocity < -1.0):
				self.y_velocity_buffer = 0.0	
		
		
			print("\ncurrent_x_velocity == " + str(self.current_x_velocity))
			print("current_y_velocity == " + str(self.current_y_velocity))
			print("x_velocity_buffer == " + str(self.x_velocity_buffer))
			print("y_velocity_buffer == " + str(self.y_velocity_buffer) + "\n")
		
		
		
		
		
		#### THIS IS THE PART YOU ARE PROBABLY THINKING ABOUT WHEN YOU ARE THINKING ABOUT MOVING ####
		
		## The math affects the FP numbers. Once the math is covered, convert the numbers back to ints.
		
		## immobility check
		if self.is_immobile:
			pass
		else:
			self.floating_point_rect_centerx = self.floating_point_rect_centerx + self.current_x_velocity
			self.floating_point_rect_centery = self.floating_point_rect_centery + self.current_y_velocity
		
		## Then actually move the thing as needed.
		self.set_centerx_and_centery_values_to_ints_of_the_floating_point_values()	
		

		if not self.is_immobile:
			print("\n\n\ncurrent_x_velocity == " + str(self.current_x_velocity))
			print("current_y_velocity == " + str(self.current_y_velocity))
			#print("rect.centerx == " + str(self.rect.centerx))
			#print("rect.centery == " + str(self.rect.centery))
			print("floating_point_rect_centerx == " + str(self.floating_point_rect_centerx))
			print("floating_point_rect_centery == " + str(self.floating_point_rect_centery) + "\n")
			
		

class Planet(GravityWell):
	''' A giant ball of rock and/or gas and/or various slippery substances. Is a GravityWell. '''
	
	## The Planet class is distinct from the GravityWell class because I want to have explorable planets with their own maps once I get the space business sorted out.

	def __init__(self, initial_x_position, initial_y_position, initial_x_velocity, initial_y_velocity, initial_mass, supplied_planet_graphic_index, is_immobile=False):

	
		## Image handling goes in the Planet class. GravityWell does not do image handling, BUT it DOES require it to be done.
	
		
		## The image component of the pygame.sprite.Sprite has to be named "image" for it to interact properly with other Sprite class methods.	
		self.image = pygame.Surface((30, 30)).convert()

		
		
		
		## DEBUG1 got to find out why colorkey isn't working the way I expect
		## First fill it with the WHITE constant.
		#self.image.fill(WHITE)
		## Then set the colorkey to WHITE. For consistency's sake, pick it up off the Surface.
		#self.image.set_colorkey(self.image.get_at((0, 0)), pygame.RLEACCEL)
	
	
		
		
		## DEBUG1 it can't be here, right?? is this where colorkey ought to go? It can't be here...!
		## DEBUG2 I think it is after the following line. Somehow.
		## thing_to_blit_to.blit(sprite_to_blit_to_the_thing, (upperleft_location_to_blit_to_on_thing_you're_blitting_to))
		self.image.blit(self.list_full_of_reference_planet_surface_objects[supplied_planet_graphic_index], (0, 0))
		
		## DEBUG2
		## Okay, so this has to be called here. BUT for some reason, the colorkey=-1 thing STILL has an effect. Specifically it turns the background black.
		## WHY!
		self.image.set_colorkey(self.image.get_at((0, 0)), pygame.RLEACCEL)
		## This has to be figured out somehow, since it isn't at all how it worked in Arinoid. Hrm.
		
		
		self.rect = self.image.get_rect()
		

		## IMPORTANT! Only init the GravityWell component AFTER you get the image and rect.
		GravityWell.__init__(self, initial_x_position, initial_y_position, initial_x_velocity, initial_y_velocity, initial_mass, is_immobile=is_immobile)	
		


class PlayingField:
	''' Define the playing field for the game. '''

	## This may be changed or added to later on. Such as when I start having to think about the two different map windows: Aurora and Outpost.
	## IMPORTANT: SEE ArinoidTest FOR DEEPEST COMMENTS EXPLAINING THIS CLASS.
	
	
	
	##~~ Scaling and centering the tile-based map ~~#
		
	## These values represent the width and height of each tile in the spritesheet:
	tile_x_pixel_measurement = 30
	tile_y_pixel_measurement = 30
	
	## The number of game-tiles in the playing field's x dimension:
	## OLD:
	#playing_field_width_in_tiles = 20
	## NEW:
	playing_field_width_in_tiles = SCREEN_BOUNDARY_RECTANGLE.width // tile_x_pixel_measurement	
	print("\nplaying_field_width_in_tiles == " + str(playing_field_width_in_tiles))
	
	## y axis:
	## OLD:
	#playing_field_height_in_tiles = 15
	## NEW:
	playing_field_height_in_tiles = SCREEN_BOUNDARY_RECTANGLE.height // tile_y_pixel_measurement
	print("\nplaying_field_height_in_tiles == " + str(playing_field_height_in_tiles))		
		
	top_x_position_offset = ((SCREEN_BOUNDARY_RECTANGLE.width // tile_x_pixel_measurement) * tile_x_pixel_measurement)
	top_y_position_offset = ((SCREEN_BOUNDARY_RECTANGLE.height // tile_y_pixel_measurement) * tile_y_pixel_measurement)
	## Note: The above operation is NOT the same as floor dividing by 1, which only shaves off fractional components if a number already has them.

	
	top_x_position_offset = ( (SCREEN_BOUNDARY_RECTANGLE.width - top_x_position_offset) // 2 )
	top_y_position_offset = ( (SCREEN_BOUNDARY_RECTANGLE.height - top_y_position_offset) // 2 )	
			
	playing_field_rectangle = pygame.Rect((tile_x_pixel_measurement + top_x_position_offset), (tile_y_pixel_measurement + top_y_position_offset), (tile_x_pixel_measurement * playing_field_width_in_tiles), (tile_y_pixel_measurement * playing_field_height_in_tiles))
	
	
	
	
	def __init__(self):
	
		## Going to keep with the .convert() on all the new Surfaces, to keep everything running fast, supposedly.
		self.playing_field_background_surface_object = pygame.Surface(SCREEN_BOUNDARY_RECTANGLE.size).convert()
	
	
	def draw_tile(self, supplied_tile_surface, x_tile_value, y_tile_value):	
		''' Use tile values provided to the PlayingField class at program initialization to display a single PlayingField tile at a specified location on the PlayingField's background_surface_object. '''
	
		## First, multiply the x and y tile placement values by the size of each tile in pixels.
		x_placement_upperleft_offset_in_pixels = (self.tile_x_pixel_measurement * x_tile_value)
		y_placement_upperleft_offset_in_pixels = (self.tile_y_pixel_measurement * y_tile_value)
	
		## Then add the border that was determined in the base Arena class values:
		x_placement_upperleft_offset_in_pixels += self.top_x_position_offset
		y_placement_upperleft_offset_in_pixels += self.top_y_position_offset
				
		## Transfer (blit) the supplied_tile_surface to the background_surface_object at the above-determined location.
		self.playing_field_background_surface_object.blit(supplied_tile_surface, (x_placement_upperleft_offset_in_pixels, y_placement_upperleft_offset_in_pixels))
		
	
	def make_background_using_one_tile_graphic(self, tile_image_index_number):
		''' Creates the playing field background out of tiles with the specified tile image index number. '''
		
		## NOTE: This assumes the background will have actual tile graphics at some point in teh Majickal Futurez one one ! spelling error self-conscious nervous laughter.
		
		## NOTE: This function creates the background for the ENTIRE playing field in ONE pass. Using ONE tile index number.
		
		for x in range(self.playing_field_width_in_tiles):		# "For each row" 
			for y in range(self.playing_field_height_in_tiles):	# "For each column"
				## OLD ---v
				## Note the + 1 in the line below -- that's because there's a one-tile-wide border around the entire PlayingField.
				#self.draw_tile(self.list_full_of_reference_tile_surface_objects[tile_image_index_number], x + 1, y + 1)
				
				## NEW ---v
				## I removed the 1-tile border.
				self.draw_tile(self.list_full_of_reference_tile_surface_objects[tile_image_index_number], x, y)
			
#### Functions ####

def calculate_gravity_and_adjust_velocities_on_all_gravity_wells(supplied_group_of_all_gravity_wells):
	for each_gravity_well_object in supplied_group_of_all_gravity_wells:
		for each_other_object in supplied_group_of_all_gravity_wells:
		
			## This prevents things from trying to gravitify themselves:			
			if each_gravity_well_object == each_other_object:
				## Print testing proves this check works perfectly.
				pass
				
			else:
			
				## With that out of the way... 
			
				## Gravity is like acceleration towards the other object's center of mass.
				## Note: In order for orbits to look cool, we have to figure out what value of acceleration is necessary to make things circle around eachother at some distance. This is very much a test and check thing untill I know the logic better.	
		
				## First, get the hypotenuse between their two centerpoints, as if it was a right triangle:
				
				adjacent = (each_gravity_well_object.floating_point_rect_centerx - each_other_object.floating_point_rect_centerx)
				opposite = (each_gravity_well_object.floating_point_rect_centery - each_other_object.floating_point_rect_centery)
				
				#print("adjacent == " + str(adjacent))
				#print("opposite == " + str(opposite))
				
				## (( NOTE!! Consider making this run faster. To save computing resources, try to only sqrt once (and only if necessary). ))
				## (( This means try an escape check for point1 == point2 (identical location)... keeping the number unsqrted untill you are done with the calcs... etc. ))
				distance_between_these_two_objects_as_a_hypotenuse = math.sqrt((adjacent ** 2) + (opposite ** 2))
				
				#print("distance_between_these_two_objects_as_a_hypotenuse == " + str(distance_between_these_two_objects_as_a_hypotenuse) + "\n")
				
				
				
				## Dummy code:
				#if adjacent >= 0.0:
				#	each_other_object.current_x_velocity += 0.01
				#elif adjacent < 0.0:
				#	each_other_object.current_x_velocity += -0.01
					
				#if opposite >= 0.0:
				#	each_other_object.current_y_velocity += 0.01
				#elif opposite < 0.0:
				#	each_other_object.current_y_velocity += -0.01
				
				## THE DUMMY CODE WORKS BEYOND MY WILDEST DREAMS.
				
				#print("each_other_object.current_x_velocity == " + str(each_other_object.current_x_velocity))
				#print("each_other_object.current_y_velocity == " + str(each_other_object.current_y_velocity))

				
				## If things are going in straight lines, it's because you're not actually making smoothly curved accelerations.
				## All those 0.01 constants ARE THE STRAIGHT LINES. :P
				## Got to use the inverse square law and the mass values to figure out what to change their velocities by.
				
				the_inverse_square_law_ratio_of_these_two_objects = ( 1 / (distance_between_these_two_objects_as_a_hypotenuse ** 2) )
				
				
				
				the_sine = adjacent / distance_between_these_two_objects_as_a_hypotenuse
				the_cosine = opposite / distance_between_these_two_objects_as_a_hypotenuse
				
				## Debug: take 2
				## Let's try dividing the sine and cosine by their sum, to get the ratios of sines and cosines per sinecosine.
				## Reason for this is just like in Asteroids. Sine and cosine are ~.71 at 45 degrees, summing to 1.42, but we need something that will modify a velocity vector without stretching it further out with extra hypotenuse length. 
				
				sum_of_sine_and_cosine = abs(the_sine) + abs(the_cosine)
				
				## The part after the * is the way we preserve the sign of the original sine and cosine. It's dividing the number by its positive version. See: [-1 / 1 = -1] and [1 / 1 = 1]
				the_sine, the_cosine = ((abs(the_sine) / sum_of_sine_and_cosine) * (the_sine / abs(the_sine))), ((abs(the_cosine) / sum_of_sine_and_cosine) * (the_cosine / abs(the_cosine)))
				
				
				print("\n\nthe_sine == " + str(the_sine))
				print("the_cosine == " + str(the_cosine))				
				
				print("the_inverse_square_law_ratio == " + str(the_inverse_square_law_ratio_of_these_two_objects))
				
				current_acceleration_value = (each_gravity_well_object.current_mass * each_other_object.current_mass) * the_inverse_square_law_ratio_of_these_two_objects
				
				print("current_acceleration_value == " + str(current_acceleration_value))
				
				## Okay, this seems to be the real problem.
				## current_acceleration_value is not supposed to be assigned to BOTH x and y velocities. It's the hypotenuse!!! -_-
				
				## debug: take 1
				## Should I just multiply it by the sine and cosine for x and y, respectively?
				## Sine is adjacent / hypotenuse... and cosine is opposite / hypotenuse...
				## So that sounds kind of truthy!
				## If sine is x_differences / hypotenuse, then multiplying the new hypotenuse-oid value (current_acceleration_value) by the sine should yield the right number.
				
				## I think it also means that the sign will be preserved and won't have to be added in, as in the old code below:
				
				## debug: take 1: OLD CODE
				#if adjacent > 0.0:
				#	each_other_object.current_x_velocity += ((current_acceleration_value_ * 50)
				#elif adjacent < 0.0:
				#	each_other_object.current_x_velocity += (-current_acceleration_value * 50)	
				#if opposite > 0.0:
				#	each_other_object.current_y_velocity += (current_acceleration_value * 50)
				#elif opposite < 0.0:
				#	each_other_object.current_y_velocity += (-current_acceleration_value * 50)
				
				## Also I'm adding a constant to it, to make it a noticeable number. Sine and cosine are ratios, and can get pretty small sometimes.
				## debug: take 1: NEW CODE
				## debug: take 2: removing the * 50 constant to see if that causes the jumping itself... or if there's something even stranger going on?
				each_other_object.current_x_velocity += ((the_sine) * current_acceleration_value)
				each_other_object.current_y_velocity += ((the_cosine) * current_acceleration_value)
				
				
				
			
		
#### The Main Program Function #### 


def main():
	''' The game's main function. Does initialization and main-looping. '''
	
	#### Initialization ####
	
	## Initialize pygame before using it.
	pygame.init()

	## Initialize the screen, using the boundary rectangle for the screen size.
	screen = pygame.display.set_mode(SCREEN_BOUNDARY_RECTANGLE.size)

	## Put a title on the window's movement bar:
	pygame.display.set_caption(WINDOW_CAPTION)			
		
	
	
	##~~ Init the Spritesheet ~~##
	
	## Make an instance of the game's spritesheet. This is the graphics of the entire game.
	the_main_spritesheet_object = Spritesheet('gravitation_test_master_spritesheet.gif')
	
	
	## And also set the graphics indices to point to specific parts of that spritesheet.
	PlayingField.list_full_of_reference_tile_surface_objects = the_main_spritesheet_object.get_multiple_images_from_this_spritesheet([	(1, 1, 30, 30)		# 0 - should look like boring old stars, for now
																																							])
	
	## Planet grafix
	Planet.list_full_of_reference_planet_surface_objects = the_main_spritesheet_object.get_multiple_images_from_this_spritesheet([	(32, 1, 30, 30)], colorkey=-1)		# 0 - this is 
																																			

	
	
	## Create the background, which for now is just a sheet of blackness.
	## Setting up a class-based system for this purpose early, so it can be interacted with later on.
	the_playing_field_object = PlayingField()		# Create the PlayingField object that the game takes place inside/infront of.
	the_playing_field_object.make_background_using_one_tile_graphic(0)			# (0) is the list_full_of_reference_tile_surface_objects[] index number of the tile that the background will be covered in.	
	
	
	GravityWell.playing_field = the_playing_field_object
	
	
	
	
	
	##~~ Create the background ~~##
	
	## This section is intended to be temporary while I get the game figured out.
	## Though it might end up being efficient to keep nearly all of the PlayingField code anyways.
	
	## Put it up on the screen even before the first RenderUpdates() call:
	screen.blit(the_playing_field_object.playing_field_background_surface_object, (0, 0))		# See the Arena class for details on the first parameter. The second is the upperleft alignment with the screen Surface() object's upperleft; the border-tweaking math comes after this in code execution and is not directly reflected in this particular pair of zeroes.
	pygame.display.update()
	
	
	

	##~~ Keep track of sprites ~~##
	
	## First make the Groups.
	
	## RenderUpdates() is special to pygame's sprite handling.
	group_of_all_sprites = pygame.sprite.RenderUpdates()
	
	## Group()s are for various iterations and assignments not native to pygame.
	group_of_gravity_wells = pygame.sprite.Group()
	group_of_planets = pygame.sprite.Group()
	
	
	## Second put the things in the Groups.
	
	GravityWell.sprite_groups_this_object_is_inside = group_of_all_sprites, group_of_gravity_wells
	## Uhh... Does having Planet as a subclass of GravityWell, and both Planet and GravityWell being in the group_of_all_sprites...
	## mean that every Planet object will be RenderUpdates()'d twice per game loop?
	## That would throw a huge monkey wrench in my assumptions about good class structuring!
	## Hope pygame knows about this and only RenderUpdates() once per Sprite regardless of multi-group inclusion.
	Planet.sprite_groups_this_object_is_inside = group_of_all_sprites, group_of_gravity_wells, group_of_planets
	## Whatever. It looks like it works, so I guess my guess was correct, and this IS how it works. Huzzah?
	

	##~~ Keep track of time ~~##
	## Initialize the clock object, used to cap the framerate / to meter the program's temporal progression.
	clock = pygame.time.Clock()
	


	##~~ The Game Loop ~~##
	
	## The game loop can be exited by using a return statement.
	while 1:

		#~ Get input ~#
		

		for event in pygame.event.get():
			## Quit events:
			## v-- clicking the X           v--- A convenient device for splitting conditionals over multiple lines!
			if event.type == pygame.QUIT	\
				or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
					## hitting the esc key --^
					return	
					
		
		if not group_of_planets:
			Planet(500, 250, 0.4, -0.4, 1, 0)
			Planet(600, 350, 0, 0, 155, 0, is_immobile=True) ## AHAH! Things need INERTIA! Mass should impart resistance to changes in velocity... Just try and make this is_immobile=False and see how it shoots off in a tango with that tiny planet, right away! Inertia should make this look much more realistic, I'd say.
			## ... possibly... inertia will end up equating to some kind of ratio that makes Force from other GravityWells adjust its Velocity less per check.
			## So relative to other GravityWells, things with inertia/mass/whatever it is will appear to change their movements more slowly.
			## But I doubt that will automatically translate into speedy orbital stabilization.
			## There is probably going to have to be a special algorithm for generating stable orbits. But if you skip straight to stable orbits, why not just make rotating circles? =\ It's true there would be elaborate orbits that look like satellite constellations... But I want to be able to change orbits mid-game!
			Planet(700, 450, -0.4, 0.4, 1, 0)		
			Planet(550, 300, 0.2, -0.2, 0.1, 0)
			
				
		#~ Clear sprites ~#
		## NOTE: The playing_field_background_surface_object should just be a giant black surface equal to the size of the screen, for now.
		
		
		group_of_all_sprites.clear(screen, the_playing_field_object.playing_field_background_surface_object)

		
		
		
		#~ Update ~#

		## Step one: The Gravitationating.
		calculate_gravity_and_adjust_velocities_on_all_gravity_wells(group_of_gravity_wells)
				
		## Step two: Rendermoving.
		group_of_all_sprites.update()

	
		#~ Redraw ~#
		## "Dirty" rectangles are when you only update things that changed, rather than the entire screen. These are the regions that have to be redrawn.
		##              [...]                     v--- Returns a list of the regions which changed since the last update()
		dirty_rectangles = group_of_all_sprites.draw(screen)
		## Once we have the changed regions, we can update specifically those:
		pygame.display.update(dirty_rectangles)
		
		
		
		#~ Cap frame rate ~#
		clock.tick(MAX_FRAMES_PER_SECOND)
			


		
#### Running the Program ####

	
## This line runs the game when the program is called up.	
if __name__ == '__main__': main()
