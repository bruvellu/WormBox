import os
import sys
from ij import IJ
from ij.gui import GenericDialog
from ij.io import OpenDialog
from math import sqrt

# Fiji only (or ImageJ+Jython).

### CLASSES ###


class Aspect:
    '''One aspect of the data set to be extracted.

    landmark_sets is a list of lists of Landmark instances.
    '''
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.landmarks_names = []
        self.landmarks = []
        self.value = None
        self.meristic = False

    def connect_landmarks(self, image):
        '''Connect selected landmarks from an image to aspect.'''
        for name in self.landmarks_names:
            for k, landmark in image.landmarks.iteritems():
                if name == landmark.name:
                    self.add_landmark(landmark)
                elif name == 'count' and landmark.name == self.name:
                    self.add_landmark(landmark)
                    self.meristic = True

    def add_landmark(self, landmark):
        '''Attach a landmark object to aspect.'''
        self.landmarks.append(landmark)

    def get_distance(self, lm_1, lm_2):
        '''Calculate distance between 2 landmarks.'''
        return sqrt((lm_1.x - lm_2.x)**2 + (lm_1.y - lm_2.y)**2)

    def calculate(self):
        '''Calculate the final value of the aspect.

        Run a check to see if any landmarks are missing. If yes, change values 
        to NA.

        self.landmarks = [landmark, landmark, (...)]
        '''
        if self.check():
            # Passed the test.
            if self.meristic:
                self.value = len(self.landmarks)
            else:
                distances = []
                n = len(self.landmarks)
                for i, landmark in enumerate(self.landmarks):
                    # Only run if not in the last iteration.
                    if not i + 2 > n:
                        distance = self.get_distance(landmark,
                                self.landmarks[i + 1])
                        distances.append(distance)
                self.value = sum(distances)
        else:
            # Failed in the test, return NA.
            self.value = 'NA'

    def check(self):
        '''Check if landmarks are missing.'''
        if self.meristic:
            return True
        else:
            expected = len(self.landmarks_names)
            observed = len(self.landmarks)
            if expected == observed:
                return True
            else:
                return False


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
        self.landmarks[landmark.id] = landmark

    def add_aspect(self, aspect):
        '''Attach an aspect object to image.'''
        self.aspects[aspect.id] = aspect

    def get_landmarks_names(self):
        '''Return the name of attached landmarks.'''
        names = [self.landmarks[id]['name'] for id in self.landmarks.keys()]
        return names


class Landmark:
    '''A landmark data point.'''
    def __init__(self, name, x, y):
        self.id = '%sx%sy%s' % (name, x, y)
        self.name = name
        self.x = float(x)
        self.y = float(y)

    def __str__(self):
        return '%s(%f, %f)' % (self.name, self.x, self.y)


### FUNCTIONS ###

def import_datafiles(folder):
    '''Import files with raw landmark data from folder.

    Scans folder for .txt files and returns paths as list.
    '''
    #TODO Try to import data directly from the image ROI set.
    # try: rois = RoiManager.getInstance().getRoisAsArray()
    # but apparently without scale...
    datafiles = []
    for file in os.listdir(folder):
        if file.endswith('_data.txt'):
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
            # Call line parser to extract values.
            filename, landmark_name, landmark_x, landmark_y = parse_data_line(line)

            # Try to catch opened image instance with filename.
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
        datafile.close()

    return images

def parse_data_line(line):
    '''Parse a single line of data and return values.'''
    # Parse raw text.
    datalist = line.split('\t')
    # Define landmark data and objects.
    names = datalist[0].split(':')
    filename = names[0]
    landmark_name = names[1].strip(' ')
    landmark_x = datalist[1]
    landmark_y = datalist[2]
    return filename, landmark_name, landmark_x, landmark_y

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
        hooks:count

    Notes:
        - Aspect name ends at ":".
        - Delimiter for landmark names is ",".
        - Line starting with "#" is ignored ("#" elsewhere is not).
        - White space before or after names are stripped, space between words are preserved. Following examples are equivalent:
            - "width : left ,far right ,  back"
            - "width:left,far right,back"
        - For meristic landmarks use name:count format (literal string count).
    '''
    aspects = []
    for line in config.readlines():
        if not line.startswith('#'):
            # Parse config line and return values.
            aspect_id, aspect_name, aspect_landmarks_names = parse_config_line(line)

            # Add aspects to images.
            for k, image in images.iteritems():
                # Create individual Aspect instance.
                aspect = Aspect(aspect_id, aspect_name)
                aspect.landmarks_names = aspect_landmarks_names
                aspect.connect_landmarks(image)
                aspect.calculate()
                image.add_aspect(aspect)

            # Save a separate instance for writing results.
            template_aspect = Aspect(aspect_id, aspect_name)
            aspects.append(template_aspect)

    return aspects

def parse_config_line(line):
    '''Parse a single line of the config file and return values.'''
    #TODO Error handling in general, parsing may fail, config file 
    # might not be in the appropriate format!
    # Strip newlines.
    this_line = line.strip('\n')
    # Split at the aspect name.
    #TODO Check if landmarks have ":" in their names?
    split_line = this_line.split(':')

    # Define aspect name stripping whitespace.
    name = split_line[0].strip(' ')
    # Split landmarks and strip whitespace.
    landmarks_names = [lm.strip(' ') for lm in split_line[1].split(',')]
    # Define Aspect id (eg "name:lm1,lm2").
    id = name + ':' + ','.join(landmarks_names)

    return id, name, landmarks_names

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

def build_header(aspect_names):
    '''Constructs ordered header labels removing duplicates.'''
    known = set()
    labels = []
    for name in aspect_names:
        if name in known:
            continue
        labels.append(name)
        known.add(name)
    return labels

def write_results(output):
    '''Write data to output file.'''
    # Write header removing duplicate aspects (will show the mean values).
    aspect_names = [aspect.name for aspect in aspects]
    labels = build_header(aspect_names)
    output.write('image,%s\n' % ','.join(labels))

    # Storing values from all images to calculate the mean/sd.
    data = {}
    # Prepopulating with empty list.
    for name in labels:
        data[name] = []

    # Just sorting images by name.
    ordered_images = [images[k] for k in sorted(images.keys())]

    for image in ordered_images:
        # Write filename.
        output.write(image.filename)
        # Local data to calculate pseudoreplicate means, if any.
        image_data = {}
        # Populate image data with raw values.
        for k, aspect in image.aspects.iteritems():
            if image_data.has_key(aspect.name):
                image_data[aspect.name].append(aspect.value)
            else:
                image_data[aspect.name] = [aspect.value]
        # Order data according to aspect names list.
        ordered_image_data = [(k, image_data[k]) for k in labels]
        # Iterate over image data and conditionally calculate means.
        for sample in ordered_image_data:
            name, values = sample[0], sample[1]
            if len(values) > 1:
                # Strip NAs
                values = [value for value in values if value != 'NA']
                # Try, because it could be a list full of NAs...
                try:
                    value = sum(values) / len(values)
                except:
                    value = 'NA'
                data[name].append(value)
            else:
                value = values[0]
                data[name].append(value)
            output.write(',' + str(value))
        output.write('\n')
        print
        print image_data
        print

    print data
    # Sort data according to aspect names list and use a bundled list 
    # comprehension to exclude NA values.
    ordered_data = [[value for value in data[k] if value != 'NA'] for k in labels]
    n_samples, means, std_devs = [], [], []
    for values in ordered_data:
        if values:
            # Define values.
            n = len(values)
            mean = sum(values) / float(n)
            sd = get_sd(values)
        else:
            # Empty values, replace by NAs.
            n, mean, sd = 'NA', 'NA', 'NA'
        # Append to lists.
        n_samples.append(str(n))
        means.append(str(mean))
        std_devs.append(str(sd))

    # Write means.
    output.write('mean,%s\n' % ','.join(means))
    # Write standard deviations.
    output.write('sd,%s\n' % ','.join(std_devs))
    # Write n samples.
    output.write('n,%s\n' % ','.join(n_samples))

def get_sd(distances):
    '''Calculate standard deviation between distances.'''
    n = len(distances)
    mean = sum(distances) / float(n)
    sums = []
    for distance in distances:
        sums.append((distance - mean)**2)
    sd = sqrt(sum(sums) / n)
    return sd

def get_config_file(folder):
    '''Returns the config file name.'''
    # Get list of files in the selected directory.
    files = os.listdir(folder)

    # Check if a config file is present in folder.
    if default_config in files:
        dialog = GenericDialog('Default config file found!')
        dialog.addMessage('Use this file for the analysis?\n \n%s' % os.path.join(folder, default_config))
        dialog.enableYesNoCancel()
        dialog.showDialog()
        if dialog.wasCanceled():
            return None
        elif dialog.wasOKed():
            return default_config
        else:
            open_dialog = OpenDialog('Select a config file', folder, default_config)
            return open_dialog.getFileName()
    else:
        # Ask user to select a config file.
        open_dialog = OpenDialog('Select a config file', folder, default_config)
        return open_dialog.getFileName()


## MAIN FUNCTION ##

#imp = IJ.getImage()
default_config = 'config.txt'

# Get directory of open image or prompt user to choose.
folder = IJ.getDirectory('image')
if not folder:
    folder = IJ.getDirectory('Select a folder')

config_filename = get_config_file(folder)

if config_filename:
    config_filepath = os.path.join(folder, config_filename)
    # Load the config file or abort.
    try:
        config = open(config_filepath)
    except:
        IJ.error('Could not open config file %s' % config_filepath)
        config = None
else:
    IJ.error('No config file was specified, aborting...')
    config = None

# Only run if config file was successfully loaded.
if config:
    # Get all raw datafiles from a folder.
    datafiles = import_datafiles(folder)

    # Extract data from text files and store in Image instances.
    images = parse_data(datafiles)

    # Parse config file and create Aspect instances.
    aspects = parse_config(images)

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
        IJ.showMessage('Error!', 'Could not write to:\n \n%s' % results_filepath)
    write_results(output)
    output.close()
    IJ.showMessage('Done!', 'See your results at:\n \n%s' % results_filepath)
