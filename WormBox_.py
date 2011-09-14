import os
import sys
from ij import IJ
from ij.gui import GenericDialog
from math import sqrt

## CLASSES ##


class Aspect:
    '''One aspect of the data set to be extracted.

    landmark_sets is a list of lists of Landmark instances.
    '''
    def __init__(self, id, name, landmark_names):
        self.id = id
        self.name = name
        self.landmark_names = landmark_names
        self.landmarks = []
        self.value = None
        self.sd = None

    def add_landmark(self, landmark):
        '''Attach a landmark object to aspect.'''
        self.landmarks.append(landmark)

    def get_distance(self, lm_1, lm_2):
        '''Calculate distance between 2 landmarks.'''
        return sqrt((lm_1.x - lm_2.x)**2 + (lm_1.y - lm_2.y)**2)

    def get_predistance(self, lm_set):
        '''Return the distance between landmarks of an image.'''
        predistances = []
        n = len(lm_set)
        for i, lm in enumerate(lm_set):
            if not i + 2 > n:
                predistance = self.get_distance(lm, lm_set[i + 1])
                predistances.append(predistance)
        return sum(predistances)

    def calculate(self):
        '''Calculate the final value of the aspect.'''
        distances = []
        n = len(self.landmark_sets)
        for lm_set in self.landmark_sets:
            predistance = self.get_predistance(lm_set)
            distances.append(predistance)
        if n > 2:
            self.sd = get_sd(distances)
        self.value = sum(distances)


class Image:
    '''Defines an image file and store landmarks and aspects.

    Landmark and Aspect objects are stored in dictionaries where the keys are 
    their names and unique ids, respectively.
    '''
    def __init__(self, filename):
        self.filename = filename
        self.landmarks = {}
        self.aspects = {}

    def add_landmark(self, landmark):
        '''Attach a landmark object to image.'''
        self.landmarks[landmark.name] = landmark

    def add_aspect(self, aspect):
        '''Attach an aspect object to image.'''
        self.aspects[aspect.id] = aspect


class Landmark:
    '''A landmark data point.'''
    def __init__(self, name, x, y):
        self.name = name
        self.x = float(x)
        self.y = float(y)

    def __str__(self):
        return '%s(%f, %f)' % (self.name, self.x, self.y)


## FUNCTIONS ##

def import_data(folder):
    '''Import files with raw landmark data from folder.

    Scans folder for .txt files and returns paths as list.
    '''
    #TODO Try to import data directly from the image ROI set.
    datafiles = []
    for file in os.listdir(folder):
        if file.endswith('.txt'):
            datafiles.append(os.path.join(folder, file))
    return datafiles

def parse_data(datafiles):
    '''Parse data from raw files.

    Read each line and instantiate objects to store data. Returns a dictionary 
    of Image instances associated with correspondent landmarks.

    Format:
        filename:landmark_name\tx_coordinate\ty_coordinate

    Example:
        Parcel01a-DSCN8755.tif:1	1.610	4.777
        Parcel01a-DSCN8755.tif:2	1.077	2.300
        Parcel01a-DSCN8755.tif:3	2.807	0.730
    '''
    images = {}
    for file in datafiles:
        datafile = open(file)
        for line in datafile.readlines():
            # Parse raw text.
            datalist = line.split('\t')
            # Define landmark data and objects.
            names = datalist[0].split(':')
            filename = names[0]
            landmark_name = names[1].strip(' ')
            landmark_x = datalist[1]
            landmark_y = datalist[2]

            # Try to catch opened instance with filename.
            try:
                image = images[filename]
            except:
                # Create image instance instead.
                image = Image(filename)
                # Add image instance to dictionary.
                images[image.filename] = image

            # Instantiate landmark object.
            landmark = Landmark(landmark_name, landmark_x, landmark_y)
            # Attach landmark to image.
            image.add_landmark(landmark)

    return images

def parse_config(images):
    '''Read config file and instantiate aspects to be analysed.

    Config format:
        name:landmark_name,landmark_name,(...)

    Example:
        width:2,4
        height:3,1
        perimeter:1,2,3,4,5
        side:1,2
        side:5,4

    Notes:
        - Aspect name ends at ":".
        - Delimiter for landmark names is ",".
        - Line starting with "#" is ignored ("#" elsewhere is not).
        - White space before or after names are stripped, space between words 
          are preserved. Following examples are equivalent:
            - "width : left ,far right ,  back"
            - "width:left,far right,back"
    '''
    for line in config.readlines():
        if not line.startswith('#'):
            #TODO Error handling in general, parsing may fail, config file 
            # might not be in the appropriate format!
            # Strip newlines.
            this_line = line.strip('\n')
            # Split at the aspect name.
            #TODO Check if landmarks have ":" in their names?
            split_line = this_line.split(':')

            # Define aspect name stripping whitespace.
            aspect_name = split_line[0].strip(' ')
            # Split landmarks and strip whitespace.
            landmark_names = [name.strip(' ') for name in 
                    split_line[1].split(',')]
            # Define Aspect id (eg "name:lm1,lm2").
            aspect_id = aspect_name + ':' + ','.join(landmark_names)

            # Add aspect to images.
            for k, image in images.iteritems():
                # Create Aspect instance.
                aspect = Aspect(aspect_id, aspect_name, landmark_names)
                image.add_aspect(aspect)

            ## Add instance to dictionary.
            #aspects[aspect_id] = aspect

            ## Get related landmarks from images.
            #for k, image in images.iteritems():
            #    lm_list = []
            #    for landmark in image.landmarks:
            #        if landmark.name in lm_names:
            #            lm_list.append(landmark)
            #    aspect.add_landmark(lm_list)

    return images

def get_results_filename():
    '''Prompt the user to suggest name of the output file.'''
    dialog = GenericDialog('Output results file')
    dialog.addStringField('Choose name without extension:', 'results')
    dialog.showDialog()
    name = dialog.getNextString()
    if dialog.wasCanceled():
        return None
    #TODO Check if file exists before and try again?
    return name + '.csv'

def write_results(images, output):
    '''Write data to output file.'''
    for k, image in images.iteritems():
        print
        print image.filename
        #print 'LANDMARKS'
        #for k, landmark in image.landmarks.iteritems():
        #    print landmark.name, landmark.x, landmark.y
        for k, aspect in image.aspects.iteritems():
            print
            print aspect.name, aspect.landmark_names
            for lm in aspect.landmarks:
                print lm.name, lm.x, lm.y
    #output.write('aspect,value,sd\n')
    #final_results = {}
    ## Calculate values and add to the final dictionary.
    #for k, aspect in aspects.iteritems():
    #    aspect.calculate()
    #    if final_results.has_key(aspect.name):
    #        final_results[aspect.name].append(aspect)
    #    else:
    #        final_results[aspect.name] = [aspect]
    ## Necessary to compilate pseudoreplicates.
    #for k, v in final_results.iteritems():
    #    if len(v) > 1:
    #        values = [aspect.value for aspect in v]
    #        mean = sum(values)/len(v)
    #        sd = get_sd(values)
    #        results.write('%s,%f,%f\n' % (k, mean, sd))
    #    else:
    #        aspect = v[0]
    #        results.write('%s,%f,%f\n' % (aspect.name, aspect.value, 
    #            aspect.sd))

def get_sd(distances):
    '''Calculate standard deviation between distances.'''
    n = len(distances)
    mean = sum(distances)/float(n)
    sums = []
    for distance in distances:
        sums.append((distance - mean)**2)
    sd = sqrt(sum(sums)/n)
    return sd

## MAIN FUNCTION ##

#imp = IJ.getImage()

# Get directory of open image or prompt user to choose.
folder = IJ.getDirectory('image')
if not folder:
    folder = IJ.getDirectory('Select a folder')

# Define configuration file and path.
config_filename = 'config'
config_filepath = os.path.join(folder, config_filename)

# Load the config file or abort.
try:
    config = open(config_filepath)
except:
    IJ.error('No config file was found at %s' % config_filepath)
    config = None


#TODO Check if lm names are correct in the config file.
#TODO Conditional for comments.
#TODO Formato para o arquivo de resultados:
#   image,aspect1,aspect2,aspect3
#   1.tif,width,height,perimeter,side(mean)
#   ...
#   mean,value,value,value
#   sd,value,value,value

# Only run if config file was successfully loaded.
if config:
    # Get all raw datafiles from a folder.
    datafiles = import_data(folder)

    # Extract data from text files and store in Image instances.
    images = parse_data(datafiles)

    # Parse config file and create Aspect instances.
    images = parse_config(images)

    # Connect aspects with landmarks and calculate.
    for k, image in images.iteritems():
        for k, aspect in image.aspects.iteritems():
            for name in aspect.landmark_names:
                try:
                    aspect.add_landmark(image.landmarks[name])
                    print image.filename, aspect.name, name
                except:
                    print 'Landmark %s absent from %s' % (name, image.filename)

    # Raise dialog to get name for results file.
    results_filename = get_results_filename()
    if not results_filename:
        IJ.showMessage('Aborting...',
                'Output file not specified (last dialog was cancelled).')
    results_filepath = os.path.join(folder, results_filename)
    try:
        output = open(results_filepath, 'wb')
    except IOError:
        output = None
    if not output:
        IJ.showMessage('Error!', 'Could not write to:\n \n%s' % 
                results_filepath)
    write_results(images, output)
    output.close()
    IJ.showMessage('Done!', 'See your results at:\n \n%s' % results_filepath)
