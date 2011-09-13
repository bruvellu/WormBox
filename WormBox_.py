import os
from ij import IJ
from math import sqrt

def get_sd(distances):
    '''Calculate standard deviation between distances.'''
    n = len(distances)
    mean = sum(distances)/float(n)
    sums = []
    for distance in distances:
        sums.append((distance - mean)**2)
    sd = sqrt(sum(sums)/n)
    return sd

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


#imp = IJ.getImage()
# Get directory of open image or choose a directory.
folder = IJ.getDirectory('image')
if not folder:
    folder = IJ.getDirectory('Select a folder')

# Configuration file
config_filename = 'config'
config_filepath = os.path.join(folder, config_filename)

# Load the config file or write rules to it.
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

if config:
    # Get all .txt files from a folder.
    datafiles = []
    for file in os.listdir(folder):
        if file.endswith('.txt'):
            datafiles.append(os.path.join(folder, file))

    # Extract data from text files.
    images = {}
    for file in datafiles:
        datafile = open(file)
        for line in datafile.readlines():
            # Parse raw text.
            datalist = line.split('\t')
            names = datalist[0].split(':')
            try:
                image = images[names[0]]
            except:
                # Create image instance.
                image = Image(names[0])
                # Add image instance to dictionary.
                images[image.filename] = image
            # Define landmark data.
            lm_name = names[1]
            lm_x = datalist[1]
            lm_y = datalist[2]
            # Instantiate landmark.
            landmark = Landmark(lm_name, lm_x, lm_y, image)
            image.add_landmark(landmark)

    aspects = {}
    for line in config.readlines():
        # Strip newlines.
        aspect_id = line.strip('\n')
        # Instantiate aspect.
        aspect = Aspect(aspect_id)
        aspects[aspect_id] = aspect
        # Get landmarks names in list.
        lm_names = aspect_id.split(',')
        lm_names.pop(0)
        # Get related landmarks from images.
        for k, image in images.iteritems():
            lm_list = []
            for landmark in image.landmarks:
                if landmark.name in lm_names:
                    lm_list.append(landmark)
            aspect.add_landmark(lm_list)

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
