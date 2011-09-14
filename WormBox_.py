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
        self.sd = None #XXX Not needed, I think.

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
            distances = []
            n = len(self.landmarks)
            for i, landmark in enumerate(self.landmarks):
                # Only run if not in the last iteration.
                if not i + 2 > n:
                    distance = self.get_distance(landmark,
                            self.landmarks[i + 1])
                    distances.append(distance)
            self.value = sum(distances)
            # Calculate standard deviation if more than 2 items.
            #XXX Not needed, I think.
            #if n > 2:
            #    self.sd = get_sd(distances)
            #else:
            #    self.sd = 'NA'
        else:
            # Failed in the test, return NA.
            self.value = 'NA'
            #self.sd = 'NA'

        #distances = []
        #n = len(self.landmark_sets)
        #for lm_set in self.landmark_sets:
        #    predistance = self.get_predistance(lm_set)
        #    distances.append(predistance)
        #if n > 2:
        #    self.sd = get_sd(distances)
        #else:
        #    self.sd = 'NA'
        #self.value = sum(distances)

    def check(self):
        '''Check if landmarks are missing.'''
        expected = len(self.landmark_names)
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
    aspects = []
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

            # Add aspects to images.
            for k, image in images.iteritems():
                lm_keys = image.landmarks.keys()
                # Create individual Aspect instance.
                aspect = Aspect(aspect_id, aspect_name, landmark_names)
                # Connect aspects with landmarks and calculate.
                for lm_name in landmark_names:
                    if lm_name in lm_keys:
                        aspect.add_landmark(image.landmarks[lm_name])
                aspect.calculate()
                image.add_aspect(aspect)

            # Save a separate instance for writing results.
            aspects.append(Aspect(aspect_id, aspect_name, landmark_names))

            ## Add instance to dictionary.
            #aspects[aspect_id] = aspect

            ## Get related landmarks from images.
            #for k, image in images.iteritems():
            #    lm_list = []
            #    for landmark in image.landmarks:
            #        if landmark.name in lm_names:
            #            lm_list.append(landmark)
            #    aspect.add_landmark(lm_list)

    return aspects

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

def write_results(output):
    '''Write data to output file.'''
    # Write header removing duplicate aspects (will showthe mean values).
    aspect_names = [aspect.name for aspect in aspects]
    aspect_names = list(set(aspect_names))
    output.write('image,%s\n' % ','.join(aspect_names))

    # Storing values from all images to calculate the mean/sd.
    data = {}
    # Prepopulating with empty list.
    for name in aspect_names:
        data[name] = []

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
        ordered_image_data = [(k, image_data[k]) for k in aspect_names]
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

    # Sort data according to aspect names list and use a bundled list 
    # comprehension to exclude NA values.
    ordered_data = [[value for value in data[k] if value != 'NA'] for k in aspect_names]
    n_samples, means, std_devs = [], [], []
    for values in ordered_data:
        # Define values.
        n = len(values)
        mean = sum(values) / n
        sd = get_sd(values)
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





    #if aspect.id == aspect_id:
    #    if not aspect.value == 'NA':
    #        data[aspect_id].append(aspect.value)
    #    output.write(',' + str(aspect.value))


    #output.write(image.filename)
    ## Use list of aspects to write in the correct order.
    #for aspect_id in aspects:
    #    data[aspect_id] = []

    #output.write('mean')
    #std_devs = []
    #ns = []
    #print data
    #for aspect_id in aspects:
    #    values = data[aspect_id]
    #    print values
    #    # Save n for next line.
    #    n = len(values)
    #    ns.append(n)
    #    # Calculate mean.
    #    print sum(values), n
    #    mean = sum(values) / n
    #    output.write(',' + str(mean))
    #    # Save standard deviation for next line.
    #    sd = get_sd(values)
    #    std_devs.append(sd)
    #output.write('\n')
    #output.write('sd')
    #for sd in std_devs:
    #    output.write(',' + str(sd))
    #output.write('\n')
    #output.write('n')
    #for n in ns:
    #    output.write(',' + str(n))

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
        IJ.showMessage('Error!', 'Could not write to:\n \n%s' % 
                results_filepath)
    write_results(output)
    output.close()
    IJ.showMessage('Done!', 'See your results at:\n \n%s' % results_filepath)
