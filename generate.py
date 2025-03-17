#!/usr/bin/env python3

import argparse
import collections
import os
import re
import shutil
import subprocess
import tempfile
import textwrap
import yaml

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--chart', required=True, help='Chart name')
    parser.add_argument('--version', required=True, help='Chart version')
    parser.add_argument('--app-version', required=True, help='Application version')
    parser.add_argument('--path', required=True, help='Path to a directory containing customization.yaml')
    parser.add_argument('--image', required=True, help='Controller image')

    args = parser.parse_args()

    temp_dir = tempfile.TemporaryDirectory()
    temp_dir_path = temp_dir.name

    chart_root = f'charts/{args.chart}'

    # Clean up so we don't leave any orphaned bits about.
    shutil.rmtree(chart_root)

    # Define directory structure.
    os.makedirs(f'{chart_root}/crds', exist_ok=True)
    os.makedirs(f'{chart_root}/templates', exist_ok=True)

    # Define chart description.
    chart = {
        'apiVersion': 'v2',
        'name': args.chart,
        'description': 'A Helm chart for deploying cluster API.',
        'type': 'application',
        'version': args.version,
        'appVersion': args.app_version,
        'icon': 'https://assets.unikorn-cloud.org/assets/images/logos/dark-on-light/icon.png',
    }

    with open(f'{chart_root}/Chart.yaml', 'w') as out:
        yaml.safe_dump(chart, out)

    # Process the official manifests.
    script_dir = os.path.dirname(os.path.realpath(__file__))
    with (
      open(f'{temp_dir_path}/kustomization.yaml', 'w') as kustomization_file,
      open(f'{script_dir}/patches.yaml', 'r') as patch_file
    ):
      patch_yaml = patch_file.read()

      print(textwrap.dedent(f'''\
        ---
        resources:
         - {args.path}

        patches:
       '''), patch_yaml, file=kustomization_file)

    content = subprocess.check_output(['kubectl', 'kustomize', temp_dir_path])

    temp_dir.cleanup()

    objects = yaml.safe_load_all(content)

    counts = collections.Counter()

    values = {
        'image': args.image,
    }

    for o in objects:
        kind = o['kind']

        # Remove erroneous fields added by upstream.
        if 'creationTimestamp' in o['metadata']:
            del o['metadata']['creationTimestamp']

        # CRDs go in a special place.
        if kind == 'CustomResourceDefinition':
            with open(f'{chart_root}/crds/{o["metadata"]["name"]}.yaml', 'w') as out:
                yaml.safe_dump(o, out)
            continue

        resource = yaml.safe_dump(o)

        # Cluster API for some reason embed environment variables in their manifests
        # because why not, it's not like everyone else uses go templating!  Replace
        # these with a values.yaml.
        matches = set(re.findall(r'\$\{.*?\}', resource))

        for m in matches:
            # https://regex101.com/r/8r9GZU/1
            fields = re.match(r'\$\{([A-Z0-9_]+)(?::=(.*))?\}', m)

            value = fields.group(1).lower()
            default = fields.group(2)

            if default == 'true':
                default = True
            elif default == 'false':
                default = False

            values[value] = default

            resource = resource.replace(m, '{{ .Values.' + value + ' }}')

        count = counts[kind]
        counts[kind] += 1

        with open(f'{chart_root}/templates/{kind.lower()}-{count}.yaml', 'w') as out:
            out.write(resource)

        with open(f'{chart_root}/values.yaml', 'w') as out:
            yaml.safe_dump(values, out)


if __name__ == '__main__':
    main()
