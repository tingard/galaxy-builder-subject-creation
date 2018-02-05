from panoptes_client import SubjectSet, Subject, Project, Panoptes
import getpass
import os
import time
# import numpy as np


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
        # comparison between model and image
        subjects[-1].add_location({'application/json': locations[1]})
        # model
        subjects[-1].add_location({'application/json': locations[2]})
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
    endpoint='https://panoptes-staging.zooniverse.org'
)
project = Project.find(1820)
subject_set = SubjectSet()
subject_set.links.project = project
subject_set.display_name = 'Test_subject_set_' + str(int(time.time()))
subject_set.save()

loc = os.path.abspath(os.path.dirname(__file__))
metadata = {
    'SDSS_ID': 1234567,
    'Ra': 0.0,
    'Dec': 0.0,
    '#isModelling': True,
    '#models': [
        {'frame': 1, 'model': 'GALAXY_BUILDER_DIFFERENCE'},
        {'frame': 2, 'model': 'GALAXY_BUILDER_MODEL'},
    ]
}

subjects = os.listdir(loc + '/subjects')
i = 0

# TODO: change subject directory structure to be more efficient
#       (not having 12,000+ files in a folder...)

if 'image_{}.png'.format(i) in subjects:
    subject_set = uploadSubjectToSet(
        project, subject_set,
        [[j.format(loc, i) for j in (
            '{}/subjects/image_{}.png',
            '{}/subjects/difference_{}.json',
            '{}/subjects/model_{}.json'
        )]],  # locations
        [{
            'SDSS_ID': '1234567',  # TODO: link this to actual ID
            'ra': 0.0000,  # TODO: link this to actual ID
            'dec': 0.0000,  # TODO: link this to actual ID
            'isModelling': True,
            'models': [
                {'frame': 1, 'model': 'GALAXY_BUILDER_DIFFERENCE'},
                {'frame': 2, 'model': 'GALAXY_BUILDER_MODEL'},
            ]
        }]  # metadata
    )
