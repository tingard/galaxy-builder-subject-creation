from panoptes_client import SubjectSet, Subject, Project, Panoptes
import getpass
import os
import time
import json
# import numpy as np


def addLocation(subjectObj, locationDict):
    fPath = next(iter(locationDict.values()))
    if os.path.isfile(fPath):
        with open(fPath, 'rb') as f:
            media_data = f.read()
        media_type = next(iter(locationDict.keys()))
        subjectObj.locations.append(media_type)
        subjectObj._media_files.append(media_data)
        return True
    return False


def uploadSubjectToSet(project, subjectSet, locationsList, metadataList):
    # imagePath can be string or list, metadata must be same dimension
    if not len(locationsList) == len(metadataList):
        print(
            '\t\033[31mInvalid arguments, locationsList and metadataList',
            'must have same length\033[0m'
        )
        return
    subjects = []
    for locations, meta in zip(locationsList, metadataList):
        subjects.append(Subject())
        subjects[-1].links.project = project
        # actual galaxy image
        subjects[-1].add_location(locations[0])
        # the json subjects need to be added in a more manual way so we can
        # spceify a MIME type
        # comparison between model and image
        addLocation(subjects[-1], {'application/json': locations[1]})
        # and now just the model
        addLocation(subjects[-1], {'application/json': locations[2]})
        for k, v in meta.items():
            subjects[-1].metadata[k] = v
        subjects[-1].save()
    subject_set.add(subjects)
    return subject_set


uname = input('Enter your username: ')
pwd = getpass.getpass()
Panoptes.connect(
    username=uname,
    password=pwd,
    endpoint='https://panoptes-staging.zooniverse.org',
    admin=True
)
project = Project.find(1820)
subject_set = SubjectSet()
subject_set.links.project = project
subject_set.display_name = 'Test_subject_set_' + str(int(time.time()))
subject_set.save()

loc = os.path.abspath(os.path.dirname(__file__))

subjects = os.listdir(loc + '/subjects')

# TODO: change subject directory structure to be more efficient
#       (not having 12,000+ files in a folder...)
for i in range(20):
    if 'image_{}.png'.format(i) in subjects:
        try:
            with open('{}/subjects/metadata_{}.json'.format(loc, i)) as f:
                metadata = json.load(f)
        except IOError:
            metadata = {}
        subject_set = uploadSubjectToSet(
            project, subject_set,
            [[j.format(loc, i) for j in (
                '{}/subjects/image_{}.png',
                '{}/subjects/difference_{}.json',
                '{}/subjects/model_{}.json'
            )]],  # locations
            [metadata],
        )
    else:
        break
