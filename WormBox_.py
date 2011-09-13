import os
from ij import IJ
from math import sqrt

## CLASSES ##


class Aspect:
    '''One aspect of the data set to be extracted.

    landmark_sets is a list of lists of Landmark instances.
    '''
    def __init__(self, id):
        self.id = id
        self.name = id.split(',')[0]
        self.landmark_sets = []
        self.value = None
        self.sd = None

    def add_landmark(self, landmark):
        '''Attach a landmark object to aspect.'''
        self.landmark_sets.append(landmark)

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
    '''Defines an image file.'''
    def __init__(self, filename):
        self.filename = filename
        self.landmarks = []

    def add_landmark(self, landmark):
        '''Attach a landmark object to image.'''
        self.landmarks.append(landmark)


class Landmark:
    '''A landmark data point.'''
    def __init__(self, name, x, y, image):
        self.name = name
        self.image = image
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
            lm_name = names[1].strip(' ')
            lm_x = datalist[1]
            lm_y = datalist[2]

            # Try to catch opened instance with filename.
            try:
                image = images[names[0]]
            except:
                # Create image instance instead.
                image = Image(names[0])
                # Add image instance to dictionary.
                images[image.filename] = image

            # Instantiate landmark object.
            landmark = Landmark(lm_name, lm_x, lm_y, image)
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
    aspects = {}

    for line in config.readlines():
        if not line.startswith('#'):
            # Strip newlines.
            this_line = line.strip('\n')
            # Split at the aspect name.
            split_line = this_line.split(':')

            # Define aspect name stripping whitespace.
            aspect_name = split_line[0].strip(' ')
            # Split landmarks and strip whitespace.
            lm_names = [name.strip(' ') for name in split_line.split(',')]

            # Define Aspect id (eg "name:lm1,lm2").
            aspect_id = aspect_name + ':' + ','.join(lm_names)
            # Create Aspect instance.
            aspect = Aspect(aspect_id)
            # Add instance to dictionary.
            aspects[aspect_id] = aspect

            # Get related landmarks from images.
            for k, image in images.iteritems():
                lm_list = []
                for landmark in image.landmarks:
                    if landmark.name in lm_names:
                        lm_list.append(landmark)
                aspect.add_landmark(lm_list)

    return aspects

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

    #TODO Fazer input para mudar o nome do arquivo dos resultados.
    # Pede nome do arquivo, se já existir avisa, sem extensão.
    results_filepath = os.path.join(folder, 'results.csv')
    results = open(results_filepath, 'wb')
    results.write('aspect,value,sd\n')
    final_results = {}
    # Calculate values and add to the final dictionary.
    for k, aspect in aspects.iteritems():
        aspect.calculate()
        if final_results.has_key(aspect.name):
            final_results[aspect.name].append(aspect)
        else:
            final_results[aspect.name] = [aspect]
    # Necessary to compilate pseudoreplicates.
    for k, v in final_results.iteritems():
        if len(v) > 1:
            values = [aspect.value for aspect in v]
            mean = sum(values)/len(v)
            sd = get_sd(values)
            results.write('%s,%f,%f\n' % (k, mean, sd))
        else:
            aspect = v[0]
            results.write('%s,%f,%f\n' % (aspect.name, aspect.value, 
                aspect.sd))
    results.close()
    IJ.showMessage('Done!', 'See your results at:\n \n%s' % results_filepath)
