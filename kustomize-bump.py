#!/usr/bin/python

import logging
import os
import re
import time
from collections import defaultdict
from distutils.util import strtobool

import crayons
import feedparser
import yaml

logging.basicConfig(
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S',
    level=logging.INFO,
)

class UpdateTags:
    def __init__(self, filepath='kustomization.yaml'):
        self.filepath = filepath
        self.yaml = None
        forbidden_words = ','.join([
            'unstable', 'latest', 'testing', 'arm64', 'arm32'
        ])
        self.forbidden_words = os.getenv('KBUMP_FORBIDDEN_WORDS', forbidden_words).split(',')

        self.nodigits = bool(strtobool(os.getenv('KBUMP_NODIGITS', '1')))

    def _read(self):
        with open(self.filepath, 'r') as f:
            self.yaml = yaml.safe_load(f)

    def _write(self):
        with open(self.filepath, 'w') as f:
            yaml.dump(self.yaml, f, default_flow_style=False)

    def maybe_modify_tag(self, target_image, new_tag):

        for image in self.yaml['images']:
            if image != target_image:
                continue

            if 'newTag' not in image:
                image['newTag'] = 'latest'

            name = crayons.yellow(image.get('newName', image.get('name')), bold=True)

            if image['newTag'] != new_tag and new_tag is not None:
                old_tag = crayons.red(image.get('newTag', 'latest'), bold=True)
                image['newTag'] = new_tag
                new_tag = crayons.green(new_tag, bold=True)
                logging.info(f'Bumped {name} from {old_tag} to {new_tag}\n')
                continue

            not_found = crayons.red('No new image found', bold=True)
            logging.info(f'{not_found} for {name}\n')

    @property
    def images(self):
        self._read()
        return self.yaml['images']


    def dockerhub_tags(self, image):
        repo = self.normalize_kustomize_image(image)[0]
        feed = feedparser.parse(f'https://rss.p.theconnman.com/{repo}.atom')

        tags = {}
        for entry in feed.entries:
            if ':' not in entry.title:
                logging.debug(f'Skipping {entry.title} due to not having a tag')
                continue

            if self.nodigits and not any(char.isdigit() for char in entry.title):
                logging.debug(f'Skipping {entry.title} due to not having digits')
                continue

            if any(bad_word in entry.title for bad_word in self.forbidden_words):
                logging.debug(f'Skipping {entry.title} due to being forbidden')
                continue

            repo, tag = entry.title.split(':')
            tags[tag] = time.mktime(entry.published_parsed)

        return tags

    def normalize_kustomize_image(self, image):
        name = image.get('newName', image.get('name'))
        tag = image.get('newTag', 'latest')

        if '/' not in name:
            name = f'library/{name}'

        return name, tag

    def slugify(self, string):
        slugs = []

        [slugs.append(item) for item in string.split('-')]
        [slugs.append(item) for item in re.findall('[a-zA-Z]+', string)]

        return slugs

    def find_target_tag(self, old_tag, new_tags):
        scores = defaultdict(int)

        if old_tag is None or isinstance(old_tag, bool):
            old_tag = 'latest'

        old_tag_time = new_tags.get(old_tag, 0)

        # Increase / decrease score due to matching slugs
        old_slugs = self.slugify(old_tag)
        for new_tag in new_tags.keys():
            for candidate_slug in self.slugify(new_tag):
                if candidate_slug in old_slugs:
                    logging.debug(f'Increasing score due to matching slug: {new_tag} {candidate_slug}')
                    scores[new_tag] += 1000
                else:
                    logging.debug(f'Decreasing score due to non matching slug: {new_tag} {candidate_slug}')
                    scores[new_tag] -= 100

        # Skip images which are older than current
        for new_tag, timestamp in new_tags.items():
            if old_tag_time > timestamp:
                logging.debug(f'Removing tag due to being older: {new_tag}')
                del scores[new_tag]

        return max(scores) if scores else None

    def run(self):
        self._read()

        for image in self.images:
            name, tag = self.normalize_kustomize_image(image)
            logging.info(f'Processing {crayons.yellow(name, bold=True)}...')

            candidate_tags = self.dockerhub_tags(image)
            target_tag = self.find_target_tag(tag, candidate_tags)
            self.maybe_modify_tag(image, target_tag)

        self._write()

if __name__ == "__main__":
    U = UpdateTags(os.getenv('KBUMP_FILEPATH', '/kustomization.yaml'))
    U.run()
