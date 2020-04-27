import os
import json
from jinja2 import Environment, FileSystemLoader


def generate_templates():
    """
    Generate REST compatible files which can be used for creating index, indexer and a custom skill set. Reads config from search-config.json and 
    uses templates from templates folder. Output files are written in http-requests folder.
    """
    out_dir = 'http-requests'
    os.makedirs(out_dir, exist_ok=True)
    with open('search-config.json', 'r') as f:
        config = json.load(f)

    for skill in config['skills']:
        for field in skill['fields']:
            if not 'type' in field:
                field['type'] = "Edm.String"

    env = Environment(loader=FileSystemLoader('templates'))

    for tmpl in ['create-index.http.tmpl', 'create-indexer.http.tmpl', 'create-skillset.http.tmpl']:
        name = '.'.join(tmpl.split('.')[:-1])
        template = env.get_template(tmpl)
        output_from_parsed_template = template.render(config)
        with open(os.path.join(out_dir, name), 'w') as f:
            f.write(output_from_parsed_template)


if __name__ == '__main__':
    generate_templates()